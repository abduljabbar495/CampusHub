# Teacher Result Portal — Setup (Bangla)

## কেন Teacher option দেখা নাও যেতে পারে?
CampusHub-এ role নির্ধারিত হয় account-এর `role` field দিয়ে, username দিয়ে নয়।
উদাহরণ: username `teacher` হলেও role যদি `STUDENT` থাকে, তাহলে Student Academic Results-ই দেখাবে।

## Admin দিয়ে Teacher role সেট করুন
1. Server চালু করে `/admin/` এ যান।
2. Superuser দিয়ে login করুন।
3. Accounts > Users থেকে সংশ্লিষ্ট account খুলুন।
4. `Role` = `Teacher` নির্বাচন করুন।
5. Teacher ID এবং Department পূরণ করুন (যদি প্রযোজ্য হয়)।
6. Save করুন।

## Teacher-কে Course assign করুন
1. Admin panel > Academics > Courses এ যান।
2. Course-এর Teacher field-এ ওই Teacher account নির্বাচন করুন।
3. Course-এর Students field-এ সংশ্লিষ্ট Student accounts নির্বাচন করুন।
4. Save করুন।

## Teacher Result Portal
Teacher account দিয়ে logout/login করার পর:
- Navbar-এ **Teacher Result Portal** দেখাবে।
- সরাসরি URL: `/academics/teacher/portal/`
- **Create Result Sheet** দিয়ে course/semester result sheet তৈরি করুন।
- Draft result sheet-এ **Bulk entry** দিয়ে পুরো ক্লাসের marks দিন।
- Marks যাচাই করে **Publish** করুন।
- Student শুধু নিজের Published Results ও CGPA দেখতে পারবে।

## Run commands
```powershell
python manage.py check
python manage.py migrate
python manage.py runserver
```

> Existing database-এর User.role পরিবর্তন করলে নতুন migration লাগে না; Admin panel থেকে record update করুন।
> Teacher portal server-side role permission দিয়ে সুরক্ষিত।
