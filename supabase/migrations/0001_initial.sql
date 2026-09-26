create extension if not exists pgcrypto;

create type conversation_status as enum ('open', 'closed', 'human');
create type lead_stage as enum ('new', 'qualified', 'proposal', 'booking', 'booked', 'lost');
create type message_direction as enum ('inbound', 'outbound');
create type booking_status as enum ('pending', 'payment_pending', 'confirmed', 'cancelled');

create table organizations (
  id uuid primary key default gen_random_uuid(),
  name varchar(200) not null,
  timezone varchar(64) not null default 'Asia/Kolkata',
  settings jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table whatsapp_accounts (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  waba_id varchar(100) not null,
  phone_number_id varchar(100) not null unique,
  display_phone_number varchar(32),
  access_token_encrypted text,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

create table customers (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  phone varchar(32) not null,
  name varchar(200),
  email varchar(320),
  profile jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (organization_id, phone)
);

create table conversations (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  customer_id uuid not null references customers(id) on delete cascade,
  whatsapp_account_id uuid not null references whatsapp_accounts(id) on delete cascade,
  status conversation_status not null default 'open',
  lead_stage lead_stage not null default 'new',
  summary text,
  last_customer_message_at timestamptz,
  window_expires_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references conversations(id) on delete cascade,
  direction message_direction not null,
  message_type varchar(40) not null,
  whatsapp_message_id varchar(160) not null unique,
  text text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table knowledge_documents (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  title varchar(300) not null,
  content text not null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table leads (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  customer_id uuid not null references customers(id) on delete cascade,
  conversation_id uuid not null references conversations(id) on delete cascade,
  destination varchar(160),
  travel_date timestamptz,
  travellers integer,
  budget numeric(12,2),
  requirements jsonb not null default '{}'::jsonb,
  stage lead_stage not null default 'new',
  created_at timestamptz not null default now()
);

create table packages (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  name varchar(200) not null,
  destination varchar(160) not null,
  duration_days integer,
  price numeric(12,2),
  currency varchar(3) not null default 'INR',
  description text,
  inclusions jsonb not null default '[]'::jsonb,
  exclusions jsonb not null default '[]'::jsonb,
  metadata jsonb not null default '{}'::jsonb,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

create table bookings (
  id uuid primary key default gen_random_uuid(),
  organization_id uuid not null references organizations(id) on delete cascade,
  customer_id uuid not null references customers(id) on delete cascade,
  package_id uuid references packages(id) on delete set null,
  travel_date timestamptz,
  travellers integer,
  amount numeric(12,2),
  currency varchar(3) not null default 'INR',
  payment_status varchar(40) not null default 'pending',
  status booking_status not null default 'pending',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table webhook_events (
  id uuid primary key default gen_random_uuid(),
  provider varchar(40) not null,
  external_event_id varchar(255) not null,
  event_type varchar(100),
  payload jsonb not null,
  processed_at timestamptz,
  created_at timestamptz not null default now(),
  unique(provider, external_event_id)
);

create index idx_whatsapp_accounts_org on whatsapp_accounts(organization_id);
create index idx_customers_org on customers(organization_id);
create index idx_conversations_org on conversations(organization_id);
create index idx_conversations_customer on conversations(customer_id);
create index idx_conversations_window on conversations(window_expires_at);
create index idx_messages_conversation_created on messages(conversation_id, created_at);
create index idx_knowledge_documents_org on knowledge_documents(organization_id);
create index idx_leads_org_stage on leads(organization_id, stage);
create index idx_packages_org_destination on packages(organization_id, destination);
create index idx_bookings_org_status on bookings(organization_id, status);
create index idx_webhook_events_provider_external on webhook_events(provider, external_event_id);

alter table organizations enable row level security;
alter table whatsapp_accounts enable row level security;
alter table customers enable row level security;
alter table conversations enable row level security;
alter table messages enable row level security;
alter table knowledge_documents enable row level security;
alter table leads enable row level security;
alter table packages enable row level security;
alter table bookings enable row level security;
alter table webhook_events enable row level security;

-- The backend currently uses a server-side database connection. Tenant-aware
-- policies will be added when dashboard authentication is introduced.
