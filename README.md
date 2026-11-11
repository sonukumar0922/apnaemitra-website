# Apna eMitra

Apna eMitra is an independent Hindi-first jobs and digital assistance website. It shares verified government/private job information, admit cards, results, schemes, document guidance, services, and study resources.

## Website and admin
- Public website: `index.html`
- Admin access: use the Admin link in the website navigation.
- Login: Firebase Authentication (Email/Password); public sign-up is not provided.
- Content database: Cloud Firestore.
- PDF/image attachments: Firebase Storage.
- Setup instructions and complete security rules: [FIREBASE_SETUP.md](./FIREBASE_SETUP.md).

## Firebase configuration status
- The Web App config for Firebase project `apna-emitra-db9cb` is now populated in `index.html`.
- Confirm the `ADMIN_UID` matches Firebase Authentication > Users.
- Publish the Firestore and Storage Rules shown in [FIREBASE_SETUP.md](./FIREBASE_SETUP.md).
- Add `apnaemitra.in` and `www.apnaemitra.in` to Firebase Authentication's Authorized domains.

## Firestore collections
The Admin dashboard manages:
`jobs`, `privateJobs`, `admitCards`, `results`, `schemes`, `services`, `documents`, and `books`.

Only documents with `status: "published"` are shown publicly. Drafts are visible to the authorized Admin only. The site listens for published content updates through Firestore listeners.

## Job discovery workflow
The repository also contains a GitHub Actions job-discovery workflow. Discovery results are leads only and must be manually checked against the recruiting organisation's official notification or careers page before publishing. Do not treat search/RSS results as proof that a vacancy is genuine or still open.

## Important limitations
- Assistance request form submission is still demo-only and is not yet stored in Firestore.
- This browser integration is protected by Firebase Security Rules; never add service-account JSON, private keys, Admin SDK credentials, or passwords to this public repository.
- Public Storage files are available to everyone. Never upload customers' Aadhaar/PAN, bank data, certificates containing personal identifiers, or other sensitive documents to `public/`.
- Test login, public reads, draft visibility, publish/edit/delete, and file upload before launch.
