# Supabase setup

Create a separate Supabase project for this repository. Do not point development at the existing TripSynk production project.

Apply migrations from `supabase/migrations/` using the Supabase CLI or SQL editor. The first migration creates the multi-tenant core schema, indexes, enum types, webhook idempotency table, and enables RLS.

The backend currently connects with a server-side PostgreSQL connection. Dashboard authentication and tenant-aware RLS policies will be added before exposing data to browser clients.
