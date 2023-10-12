create table
  public.barrel_wishlist (
    id bigint generated by default as identity,
    sku text not null,
    amount integer null default 0,
    priority integer null default 0,
    constraint barrel_wishlist_pkey primary key (id)
  ) tablespace pg_default;

  create table
  public.barrels (
    sku text not null,
    ml_per_barrel integer not null default 0,
    potion_type integer[] not null default '{1,0,0,0}'::integer[],
    price integer not null default 0,
    quantity integer not null default 10,
    constraint barrels_pkey primary key (sku)
  ) tablespace pg_default;

  create table
  public.cart_items (
    id bigint generated by default as identity,
    cart_id bigint not null,
    item_sku text null,
    amount integer null default 0,
    when_created timestamp with time zone not null default (now() at time zone 'pst'::text),
    historic_price integer null,
    constraint cart_items_pkey primary key (id),
    constraint cart_items_cart_id_fkey foreign key (cart_id) references carts (cart_id) on update cascade on delete cascade,
    constraint cart_items_item_sku_fkey foreign key (item_sku) references inventory (sku) on update cascade on delete cascade
  ) tablespace pg_default;

  create table
  public.carts (
    cart_id bigint generated by default as identity,
    customer_name text null,
    payment text null,
    constraint carts_pkey primary key (cart_id)
  ) tablespace pg_default;

  create table
  public.ingredients (
    id bigint generated by default as identity,
    sku text not null,
    ingredient_order smallint null,
    constraint ingredients_pkey primary key (id),
    constraint ingredients_sku_fkey foreign key (sku) references inventory (sku) on update cascade on delete cascade
  ) tablespace pg_default;

  create table
  public.inventory (
    stock integer not null default 0,
    name text not null default '""'::text,
    sku text not null,
    constraint inventory_pkey primary key (sku),
    constraint inventory_sku_key unique (sku)
  ) tablespace pg_default;

  create table
  public.launch_codes (
    code text not null,
    stringish text not null default 'unused'::text,
    intish integer null,
    active boolean not null default false,
    constraint launch_codes_pkey primary key (code)
  ) tablespace pg_default;

  create table
  public.potions (
    id bigint generated by default as identity,
    sku text not null,
    price integer not null default 0,
    recipe integer[] not null default '{0,0,0,0}'::integer[],
    constraint potions_pkey primary key (id),
    constraint potions_sku_fkey foreign key (sku) references inventory (sku) on update cascade on delete cascade
  ) tablespace pg_default;

  create table
  public.potions_wishlist (
    id bigint generated by default as identity,
    potion_id bigint not null,
    amount integer null default 0,
    priority integer not null default 0,
    constraint potions_wishlist_pkey primary key (id),
    constraint potions_wishlist_potion_id_fkey foreign key (potion_id) references potions (id) on update cascade on delete cascade
  ) tablespace pg_default;