# CampusHub — FR-05, FR-07 ও FR-09 Implementation Guide

এই আপডেটে Module 1-এর FR-04 Academic Results-এর বিদ্যমান code/model/template অপরিবর্তিত রাখা হয়েছে। Module 2-এর FR-05 ও FR-07 এবং Module 3-এর FR-09-এর workflow ও UI উন্নত করা হয়েছে।

## FR-05 — Course Materials
- Teacher নিজের assigned course-এ material upload করতে পারবেন।
- Student শুধু নিজের enrolled course-এর material দেখতে ও download করতে পারবেন।
- Admin সব course-এর materials manage করতে পারবেন।
- File type allowlist ও 10 MB size limit form validation-এ আছে।
- Download view role এবং course enrollment/assignment যাচাই করে।

## FR-07 — Notices & Events
- STAFF ও ADMIN notice/event তৈরি এবং publish করতে পারবেন।
- Student/Teacher সাধারণত শুধু published notice এবং upcoming published event দেখবেন।
- Staff/Admin draft-ও দেখতে পারবেন।
- Notice category, priority, attachment, event date/time/location এবং search/filter আছে।
- Delete action POST + CSRF protected।

## FR-09 — Visitor Management
- SECURITY ও ADMIN visitor register করতে পারবেন।
- Registration-এর পর unique UUID pass এবং QR image তৈরি হয়।
- QR link security-authenticated scan page-এ যায়।
- Security/Admin check-in ও check-out record করতে পারবেন।
- Visitor list-এ search, status filter ও date filter আছে।
- Phone/photo validation যুক্ত হয়েছে।

## Important demo limitation
QR image-এ current host URL encode হয়। একই PC-তে local demo করলে localhost URL কাজ করবে। অন্য ফোন দিয়ে scan করতে চাইলে development server-কে একই Wi-Fi network-এ accessible করতে হবে এবং QR URL-এ PC-এর LAN IP ব্যবহার করতে হবে। এই implementation camera-based in-browser scanner নয়; ফোনের QR reader দিয়ে URL open করে security login-এর পর action করতে হবে।

## Install/update
1. Project-এর backup রাখুন।
2. ZIP extract করে inner `CampusHub` folder-এর contents আপনার working project-এ copy করুন।
3. `.venv` delete করবেন না; `.env` থাকলে সেটিও preserve করবেন।
4. Project root (যেখানে `manage.py`) থেকে:
   ```powershell
   python manage.py check
   python manage.py makemigrations
   python manage.py migrate
   python manage.py runserver
   ```
5. Existing migrations/model fields পরিবর্তন করা হয়নি এই FR implementation-এর জন্য; `makemigrations` কোনো migration তৈরি না করলেও সেটি স্বাভাবিক।

## Routes
- FR-04 Results: `/academics/results/`
- FR-05 Materials: `/materials/`
- FR-05 Upload: `/materials/upload/`
- FR-07 Notices: `/campus/notices/`
- FR-07 Events: `/campus/events/`
- FR-09 Visitors: `/visitors/`


ডাটাবেস নোট: এই build-এ SQLite ব্যবহার করা হয়েছে। `db.sqlite3` ফাইলটি `manage.py`-এর পাশে তৈরি হবে। XAMPP/MySQL configuration প্রয়োজন নেই।
