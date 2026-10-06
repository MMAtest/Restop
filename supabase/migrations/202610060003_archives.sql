create or replace function public.restop_archive_item(p_restaurant_id uuid,p_item_id uuid,p_item_type text,p_reason text)
returns uuid language plpgsql security invoker set search_path=public as $$
declare table_name text; snapshot jsonb; ingredients jsonb; archive_id uuid;
begin
 table_name:=case p_item_type when 'produit' then 'restop_products' when 'fournisseur' then 'restop_suppliers' when 'production' then 'restop_recipes' when 'preparation' then 'restop_preparations' else null end;
 if table_name is null then raise exception 'Type invalide'; end if;
 execute format('select to_jsonb(t) from %I t where id=$1 and restaurant_id=$2 for update',table_name) into snapshot using p_item_id,p_restaurant_id;
 if snapshot is null then raise exception 'Élément introuvable'; end if;
 if p_item_type='produit' and not (snapshot->>'active')::boolean then raise exception 'Produit déjà archivé'; end if;
 if p_item_type='production' then select coalesce(jsonb_agg(to_jsonb(i)),'[]'::jsonb) into ingredients from restop_recipe_ingredients i where recipe_id=p_item_id and restaurant_id=p_restaurant_id; snapshot:=snapshot||jsonb_build_object('_ingredients',ingredients); end if;
 snapshot:=snapshot||jsonb_build_object('nom',snapshot->>'name');
 insert into restop_archives(restaurant_id,original_id,item_type,original_data,reason) values(p_restaurant_id,p_item_id,p_item_type,snapshot,p_reason) returning id into archive_id;
 if p_item_type='produit' then update restop_products set active=false where id=p_item_id and restaurant_id=p_restaurant_id;
 else execute format('delete from %I where id=$1 and restaurant_id=$2',table_name) using p_item_id,p_restaurant_id; end if;
 return archive_id;
end $$;
create or replace function public.restop_restore_item(p_restaurant_id uuid,p_archive_id uuid)
returns uuid language plpgsql security invoker set search_path=public as $$
declare archive restop_archives; table_name text;
begin
 select * into archive from restop_archives where id=p_archive_id and restaurant_id=p_restaurant_id for update;
 if archive.id is null then raise exception 'Archive introuvable'; end if;
 table_name:=case archive.item_type when 'produit' then 'restop_products' when 'fournisseur' then 'restop_suppliers' when 'production' then 'restop_recipes' when 'preparation' then 'restop_preparations' else null end;
 if table_name is null or archive.original_data->>'restaurant_id'<>p_restaurant_id::text then raise exception 'Archive invalide'; end if;
 if archive.item_type='produit' then update restop_products set active=true where id=archive.original_id and restaurant_id=p_restaurant_id; if not found then raise exception 'Produit archivé introuvable'; end if;
 else execute format('insert into %I select * from jsonb_populate_record(null::%I,$1)',table_name,table_name) using archive.original_data; end if;
 if archive.item_type='production' then insert into restop_recipe_ingredients select * from jsonb_populate_recordset(null::restop_recipe_ingredients,coalesce(archive.original_data->'_ingredients','[]'::jsonb)); end if;
 delete from restop_archives where id=archive.id and restaurant_id=p_restaurant_id;
 return archive.original_id;
end $$;
revoke all on function public.restop_archive_item(uuid,uuid,text,text) from public,anon,authenticated;
revoke all on function public.restop_restore_item(uuid,uuid) from public,anon,authenticated;
grant execute on function public.restop_archive_item(uuid,uuid,text,text) to service_role;
grant execute on function public.restop_restore_item(uuid,uuid) to service_role;
