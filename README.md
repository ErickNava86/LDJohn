# Line Dancing John — LDJ-021

LDJ-021 moves admin-uploaded event images and editable event metadata off Render's temporary filesystem and into Cloudinary.

## What changed

- Event covers upload to Cloudinary.
- Gallery photos upload to Cloudinary.
- Cover replacement overwrites the same Cloudinary public ID.
- Photo deletion removes the Cloudinary asset and its JSON entry.
- Event deletion removes all of that event's Cloudinary assets.
- `events.json` is mirrored to Cloudinary as a raw JSON asset after every admin change.
- On startup, the app restores the newest Cloudinary copy of `events.json`.
- Existing local images remain supported until the one-time migration is run.

## Local setup

1. Copy `.env.example` to `.env`.
2. Fill in all six values.
3. Create a virtual environment and install requirements:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate
python -m pip install -r requirements.txt
```

## One-time migration

With `.env` configured, upload all existing local event images and persist the converted event data:

```powershell
python migrate_to_cloudinary.py
```

Do not run the migration repeatedly unless you intentionally want to overwrite the Cloudinary assets using the current local event-image folders.

## Run locally

```powershell
python run.py
```

Test the full admin workflow before deployment:

1. Add a test event with a cover and multiple gallery photos.
2. Replace its cover.
3. Add more gallery photos.
4. Delete one gallery photo.
5. Delete the test event.
6. Restart Flask and confirm the remaining events still load from Cloudinary.

## Render environment variables

Add the same six variables to Render before deployment:

- `SECRET_KEY`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`

Never commit `.env`.
