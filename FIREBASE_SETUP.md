# Apna eMitra Firebase integration

## Files changed
- `index.html`: Firebase Authentication, Firestore Admin content manager, Storage upload, and public live content listeners.

## Before using the Admin panel
1. Open `index.html` in GitHub.
2. In the Firebase module, replace the five `PASTE_...` values in `firebaseConfig` using Firebase Console > Project settings > General > Your apps > SDK setup and configuration > Config.
3. `ADMIN_UID` is prefilled with the UID supplied during setup. Confirm it exactly matches Authentication > Users.
4. Commit the changes.

## Firebase Authentication
- Enable Email/Password provider.
- Create the admin user in Authentication > Users.
- Authentication > Settings > Authorized domains: add `apnaemitra.in` and `www.apnaemitra.in`. Add your GitHub Pages hostname too if testing there.

## Firestore Rules
The Firestore Rules must protect every collection used by the dashboard. In addition to the rules already configured, include:

```javascript
match /privateJobs/{id} {
  allow read: if isAdmin() || resource.data.status == "published";
  allow create, update, delete: if isAdmin();
}
```

The dashboard uses these collections:
`jobs`, `privateJobs`, `admitCards`, `results`, `schemes`, `services`, `documents`, `books`.

For public pages, the code queries only documents where `status == "published"`. Draft records are not displayed to visitors. The admin can read drafts after successful sign-in with the configured UID.

## Storage
- Confirm the Storage Rules use the same Admin UID.
- Public attachments are uploaded under `public/<collection>/...`.
- The first version permits PDF and common image files up to 10 MB.
- Do not upload Aadhaar, PAN, bank details, certificates containing personal identifiers, or other private customer documents to the public folder.

## Important
- Firebase web config is intended to be included in client-side web apps, but do not add service-account JSON, private keys, passwords, or Admin SDK credentials to this repository.
- This is a browser-client integration protected by Firebase Rules; it is not a replacement for a trusted backend for sensitive operations.
- Assistance request submission is still demo-only and will be connected separately with privacy-conscious request rules.
- Verify the website on the custom domain after deployment, and test: public read, admin login, draft visibility, publish, edit, delete, and file upload.
