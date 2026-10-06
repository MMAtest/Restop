-- Atomic recipe and ingredient replacement. Only the authenticated Edge API service may invoke it.
create or replace function public.restop_save_recipe(p_restaurant_id uuid,p_recipe_id uuid,p_payload jsonb)
returns uuid language plpgsql security invoker set search_path = public as $$
declare saved_id uuid; ingredient jsonb; product_id uuid;
begin
  if nullif(trim(p_payload->>'nom'),'') is null or (p_payload->>'portions')::integer <= 0 then raise exception 'Nom et portions valides requis'; end if;
  if p_recipe_id is null then
    insert into restop_recipes(restaurant_id,name,description,category,portions,preparation_time,instructions,selling_price,planned_coefficient)
    values(p_restaurant_id,trim(p_payload->>'nom'),p_payload->>'description',p_payload->>'categorie',(p_payload->>'portions')::integer,nullif(p_payload->>'temps_preparation','')::integer,p_payload->>'instructions',nullif(p_payload->>'prix_vente','')::numeric,nullif(p_payload->>'coefficient_prevu','')::numeric) returning id into saved_id;
  else
    update restop_recipes set name=trim(p_payload->>'nom'),description=p_payload->>'description',category=p_payload->>'categorie',portions=(p_payload->>'portions')::integer,preparation_time=nullif(p_payload->>'temps_preparation','')::integer,instructions=p_payload->>'instructions',selling_price=nullif(p_payload->>'prix_vente','')::numeric,planned_coefficient=nullif(p_payload->>'coefficient_prevu','')::numeric,updated_at=now() where id=p_recipe_id and restaurant_id=p_restaurant_id returning id into saved_id;
    if saved_id is null then raise exception 'Recette introuvable'; end if;
    delete from restop_recipe_ingredients where recipe_id=saved_id and restaurant_id=p_restaurant_id;
  end if;
  for ingredient in select value from jsonb_array_elements(coalesce(p_payload->'ingredients','[]'::jsonb)) loop
    product_id := coalesce(ingredient->>'ingredient_id',ingredient->>'produit_id')::uuid;
    if ingredient->>'ingredient_type'='preparation' or (ingredient->>'quantite')::numeric <= 0 then raise exception 'Ingrédient invalide'; end if;
    if not exists(select 1 from restop_products where id=product_id and restaurant_id=p_restaurant_id and active) then raise exception 'Produit introuvable dans ce restaurant'; end if;
    insert into restop_recipe_ingredients(restaurant_id,recipe_id,product_id,product_name,quantity,unit)
    values(p_restaurant_id,saved_id,product_id,coalesce(ingredient->>'ingredient_nom',ingredient->>'produit_nom'),(ingredient->>'quantite')::numeric,ingredient->>'unite');
  end loop;
  return saved_id;
end $$;
revoke all on function public.restop_save_recipe(uuid,uuid,jsonb) from public,anon,authenticated;
grant execute on function public.restop_save_recipe(uuid,uuid,jsonb) to service_role;
