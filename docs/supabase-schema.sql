-- Esquema Supabase para JAH AI.
-- Ejecuta este SQL en Supabase SQL Editor antes de activar AUTH_PROVIDER=supabase.

create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null,
  name text not null default '',
  avatar_url text not null default '',
  role text not null default 'user',
  plan text not null default 'Gratis',
  preferences jsonb not null default '{}'::jsonb,
  last_login timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.conversation_history (
  id bigserial primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  session_id text not null,
  chat_id text not null default '',
  user_message text not null,
  ai_response text not null,
  sources jsonb not null default '[]'::jsonb,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.conversation_summaries (
  id bigserial primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  session_id text not null,
  summary text not null default '',
  metadata jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now(),
  unique (user_id, session_id)
);

create index if not exists profiles_email_idx on public.profiles (email);
create index if not exists conversation_history_user_created_idx
  on public.conversation_history (user_id, created_at desc);
create index if not exists conversation_history_session_idx
  on public.conversation_history (session_id);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists profiles_set_updated_at on public.profiles;
create trigger profiles_set_updated_at
before update on public.profiles
for each row
execute function public.set_updated_at();

alter table public.profiles enable row level security;
alter table public.conversation_history enable row level security;
alter table public.conversation_summaries enable row level security;

drop policy if exists "profiles_select_own" on public.profiles;
create policy "profiles_select_own"
on public.profiles for select
using (auth.uid() = id);

drop policy if exists "profiles_update_own" on public.profiles;
create policy "profiles_update_own"
on public.profiles for update
using (auth.uid() = id)
with check (auth.uid() = id);

drop policy if exists "history_select_own" on public.conversation_history;
create policy "history_select_own"
on public.conversation_history for select
using (auth.uid() = user_id);

drop policy if exists "history_insert_own" on public.conversation_history;
create policy "history_insert_own"
on public.conversation_history for insert
with check (auth.uid() = user_id);

drop policy if exists "summaries_select_own" on public.conversation_summaries;
create policy "summaries_select_own"
on public.conversation_summaries for select
using (auth.uid() = user_id);

drop policy if exists "summaries_upsert_own" on public.conversation_summaries;
create policy "summaries_upsert_own"
on public.conversation_summaries for all
using (auth.uid() = user_id)
with check (auth.uid() = user_id);
