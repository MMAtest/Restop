create or replace function public.restop_record_movement(p_restaurant_id uuid,p_user_id uuid,p_payload jsonb)
returns jsonb language plpgsql security invoker set search_path=public as $$
declare product restop_products; qty numeric; target numeric; kind text; movement restop_stock_movements;
begin
 select * into product from restop_products where id=(p_payload->>'produit_id')::uuid and restaurant_id=p_restaurant_id and active for update;
 if product.id is null then raise exception 'Produit introuvable'; end if;
 qty:=(p_payload->>'quantite')::numeric; kind:=case p_payload->>'type' when 'entree' then 'in' when 'sortie' then 'out' when 'ajustement' then 'adjustment' else null end;
 if kind is null or qty is null or qty<0 or (kind<>'adjustment' and qty=0) then raise exception 'Quantité ou type invalide'; end if;
 if nullif(p_payload->>'unite','') is not null and p_payload->>'unite'<>product.unit then raise exception 'Utilisez l’unité de stock du produit'; end if;
 target:=case kind when 'in' then product.current_stock+qty when 'out' then product.current_stock-qty else qty end;
 if target<0 then raise exception 'Stock insuffisant'; end if;
 insert into restop_stock_movements(restaurant_id,product_id,movement_type,quantity,unit,reason,performed_by) values(p_restaurant_id,product.id,kind,qty,product.unit,coalesce(p_payload->>'commentaire',p_payload->>'reference'),p_user_id) returning * into movement;
 update restop_products set current_stock=target,updated_at=now() where id=product.id and restaurant_id=p_restaurant_id;
 return jsonb_build_object('id',movement.id,'produit_id',product.id,'produit_nom',product.name,'type',p_payload->>'type','quantite',qty,'date',movement.created_at);
end $$;
revoke all on function public.restop_record_movement(uuid,uuid,jsonb) from public,anon,authenticated;
grant execute on function public.restop_record_movement(uuid,uuid,jsonb) to service_role;

create or replace function public.restop_confirm_invoice(p_restaurant_id uuid,p_payload jsonb)
returns jsonb language plpgsql security invoker set search_path=public as $$
declare doc restop_documents; item jsonb; product restop_products; supplier uuid; product_id uuid; qty numeric; price numeric; unit text; created_count integer:=0; entry_count integer:=0;
begin
 select * into doc from restop_documents where id=(p_payload->>'document_id')::uuid and restaurant_id=p_restaurant_id for update;
 if doc.id is null then raise exception 'Document introuvable'; end if;
 if doc.document_type<>'facture_fournisseur' then raise exception 'Ce document n’est pas une facture fournisseur'; end if;
 if doc.status='integre' then return jsonb_build_object('success',true,'already_imported',true,'message','Cette facture a déjà été intégrée. Le stock n’a pas été modifié.'); end if;
 if jsonb_array_length(coalesce(p_payload->'items','[]'::jsonb))=0 then raise exception 'Aucune ligne à importer'; end if;
 supplier:=nullif(p_payload->>'supplier_id','')::uuid;
 if supplier is not null and not exists(select 1 from restop_suppliers where id=supplier and restaurant_id=p_restaurant_id) then raise exception 'Fournisseur introuvable'; end if;
 if supplier is null and coalesce((p_payload->>'create_supplier')::boolean,false) then
  if nullif(trim(p_payload->>'supplier_name'),'') is null then raise exception 'Nom de fournisseur requis'; end if;
  insert into restop_suppliers(restaurant_id,name,categories) values(p_restaurant_id,p_payload->>'supplier_name',array[coalesce(p_payload->>'supplier_category','frais')]) returning id into supplier;
 end if;
 -- Sort product locks consistently across concurrent imports.
 for item in select value from jsonb_array_elements(p_payload->'items') order by coalesce(value->>'selected_product_id',value->>'product_id','') loop
  qty:=coalesce(item->>'final_qty',item->>'ocr_qty')::numeric;
  price:=coalesce(item->>'final_price',item->>'ocr_price','0')::numeric;
  if qty is null or qty<=0 or price<0 then raise exception 'Quantité ou prix invalide'; end if;
  product_id:=coalesce(nullif(item->>'selected_product_id',''),nullif(item->>'product_id',''))::uuid;
  product:=null;
  if product_id is not null then
   select * into product from restop_products where id=product_id and restaurant_id=p_restaurant_id and active for update;
   if product.id is null then raise exception 'Produit introuvable dans ce restaurant'; end if;
  else
   if nullif(trim(coalesce(item->>'final_name',item->>'ocr_name')),'') is null then raise exception 'Nom de produit requis'; end if;
   insert into restop_products(restaurant_id,name,category,unit,unit_price,reference_price,supplier_id,main_supplier_id,current_stock,min_stock,target_stock,active)
   values(p_restaurant_id,coalesce(item->>'final_name',item->>'ocr_name'),'Import OCR',coalesce(item->>'final_unit',item->>'ocr_unit','kg'),price,price,supplier,supplier,0,0,0,true) returning * into product;
   created_count:=created_count+1;
  end if;
  unit:=coalesce(nullif(item->>'final_unit',''),nullif(item->>'ocr_unit',''),product.unit);
  if unit<>product.unit then raise exception 'Unité incompatible avec le produit %',product.name; end if;
  update restop_products set current_stock=coalesce(current_stock,0)+qty,unit_price=price,reference_price=price,updated_at=now() where id=product.id and restaurant_id=p_restaurant_id;
  insert into restop_stock_movements(restaurant_id,product_id,movement_type,quantity,unit,reason) values(p_restaurant_id,product.id,'in',qty,unit,'Import facture '||doc.id::text);
  insert into restop_product_batches(restaurant_id,product_id,supplier_id,quantity,initial_quantity,unit,expiry_date,batch_number)
   values(p_restaurant_id,product.id,supplier,qty,qty,unit,nullif(item->>'dlc','')::date,coalesce(nullif(item->>'batch_number',''),'REC-'||substr(gen_random_uuid()::text,1,8)));
  entry_count:=entry_count+1;
 end loop;
 update restop_documents set status='integre',updated_at=now() where id=doc.id and restaurant_id=p_restaurant_id;
 return jsonb_build_object('success',true,'message','Import validé et stock mis à jour','stats',jsonb_build_object('products_created',created_count,'stock_entries',entry_count,'batches_created',entry_count));
end $$;
revoke all on function public.restop_confirm_invoice(uuid,jsonb) from public,anon,authenticated;
grant execute on function public.restop_confirm_invoice(uuid,jsonb) to service_role;
