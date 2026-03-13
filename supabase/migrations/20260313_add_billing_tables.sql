-- Billing schema for seller subscriptions and explicit profile billing state.

alter table if exists public.profiles
  add column if not exists billing_plan text not null default 'free',
  add column if not exists billing_status text not null default 'active',
  add column if not exists billing_interval text not null default 'month',
  add column if not exists billing_provider text,
  add column if not exists billing_email text,
  add column if not exists razorpay_customer_id text,
  add column if not exists razorpay_subscription_id text,
  add column if not exists plan_started_at timestamptz,
  add column if not exists current_period_start timestamptz,
  add column if not exists current_period_end timestamptz,
  add column if not exists trial_started_at timestamptz,
  add column if not exists trial_ends_at timestamptz;

create table if not exists public.subscriptions (
  id uuid primary key default gen_random_uuid(),
  seller_id uuid not null references public.profiles(id) on delete cascade,
  plan_id text not null,
  status text not null default 'pending',
  provider text not null default 'manual',
  amount_inr integer not null default 0,
  currency text not null default 'INR',
  provider_order_id text,
  provider_payment_id text,
  provider_subscription_id text,
  current_period_start timestamptz,
  current_period_end timestamptz,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists subscriptions_seller_id_idx on public.subscriptions (seller_id);
create index if not exists subscriptions_created_at_idx on public.subscriptions (created_at desc);
create index if not exists subscriptions_status_idx on public.subscriptions (status);
