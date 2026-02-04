# Notifications migration fix (production: uuid to bigint error)

## What was wrong
Production has `DeviceToken` with a **UUID** primary key. The auto-generated migration tried to change `id` to **bigint**, which PostgreSQL rejects (`cannot cast type uuid to bigint`).

## What we changed
1. **Model**  
   `DeviceToken` now explicitly uses a **UUID** primary key so it matches production and migrations no longer try to change `id`.

2. **Migrations**  
   - `0002_remove_devicetoken_token_unique` – only removes the unique constraint on `token` (no change to `id`).
   - `0003_devicetoken_uuid_id_state` – updates only Django’s migration state so `DeviceToken.id` is treated as UUID; no database change.

## What to do on production

1. **Remove the broken migration**  
   Delete (or move aside) the migration that failed, e.g.:
   - `notifications/migrations/0002_remove_notification_notificatio_recipie_2d3764_idx_and_more.py`

2. **Deploy this code**  
   Ensure the repo has:
   - `DeviceToken` with `id = models.UUIDField(primary_key=True, ...)`
   - `0002_remove_devicetoken_token_unique.py`
   - `0003_devicetoken_uuid_id_state.py`

3. **Run migrations**
   ```bash
   python manage.py migrate notifications
   ```
   This will apply:
   - `0002` – alter `token` (drop unique) only; no change to `id`.
   - `0003` – state-only update so `id` is UUID in the migration state.

4. **If you still have old notification models**  
   If your DB still has `Notification` / `NotificationPreference` (or similar) from an older app version, you can either:
   - Leave the tables in place (they are unused), or
   - Add a later migration to drop them after confirming nothing else uses them.

## New installs (no existing notifications DB)
For a fresh database, ensure the first migration that creates `DeviceToken` uses a UUID primary key. If your current `0001_initial` uses `BigAutoField`, you can either:
- Change `0001_initial` to use `UUIDField` for `DeviceToken.id`, or
- Rely on `0003` after applying `0001` and `0002` so the state matches the model (only if you did not create the table with UUID in 0001; for new installs, aligning 0001 with the model is cleaner).
