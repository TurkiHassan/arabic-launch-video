# Intake: talk before you build

Most people running this skill are not developers. They know what they want to show, not
what a composition or an API key is. The interview turns that into a brief you can build
from, and surfaces everything the video will need (files, links, keys) **before** any work
starts, so the run never stalls halfway on a missing logo or key.

Ask with `AskUserQuestion` (2-4 questions per round, plain Arabic unless the user writes in
English, one short line of "why" per option). Skip any question the user already answered
in their request or that the project itself answers (a repo with a logo and a Tailwind
palette does not need round 3's brand questions). Never ask for an API key in chat.

## Round 1 — the goal

1. **What are we making?**
   - إعلان إطلاق لمنتج أو تطبيق (the default: hook → reveal → how it works → value → CTA)
   - إعلان لميزة جديدة داخل منتج قائم (narrower: one feature, deeper)
   - فيديو تعريفي أو تعليمي قصير (explainer pacing: calmer, more on-screen text time)
   - تعليق صوتي عربي فقط على فيديو جاهز → hand off to the `arabic-voiceover` skill
2. **What do we build it from?**
   - مشروع موجود في هذا المجلد (read the code: real copy, colors, fonts, screens)
   - رابط موقع أو صفحة متجر (fetch it for copy, colors, screenshots)
   - صور وملفات سأرسلها (screenshots, logo, brand sheet)
   - وصف فقط، لا شيء جاهز (you will design the UI mockups from the description)
3. **Where will it be posted?** → format
   - تيك توك / ريلز / سناب / ستوري → عمودي 1080×1920 (default)
   - يوتيوب / عرض على شاشة / موقع → أفقي 1920×1080
   - منشور إكس أو لينكدإن → مربع 1080×1080
4. **How long?** 15 ث (hook + CTA only) · 20-25 ث (default) · 30-35 ث (more features)

## Round 2 — the voice (the part people ask about most)

1. **Narration?**
   - نعم، تعليق فصيح بصوت آلي (continue below)
   - سأسجّله بصوتي (they record `vo1.m4a…voN.m4a` from the script you write; see arabic-voice.md → "Own voice")
   - بدون تعليق، موسيقى ونص فقط
2. **Which engine?** Recommend by what they have, not by what is best in the abstract:
   - **Gemini — صوت Charon (Recommended)**: the most natural فصحى here; needs a free Google key (2 minutes, no card).
   - **edge-tts — مجاني فورًا بلا أي تسجيل**: good for a first try; flatter read.
   - **ElevenLabs — Haytham**: paid plan for API use; free accounts can generate by hand on the site.
3. **Voice & tone**: رجل / امرأة · هادئ واثق / حماسي / رسمي. (Gemini male: Charon, Algieba, Iapetus, Orus; female: Kore, Aoede. edge-tts: ar-SA-HamedNeural / ar-SA-ZariyahNeural.)
4. **Their own words?** "هل لديك نص تريد قوله حرفيًا؟" If yes, you diacritize and lightly edit it for timing, and show them the result before generating.

## Round 3 — materials and facts

Ask only for what the source in round 1 did not give you.

1. **Logo** (SVG best, else a large PNG) and **app icon**.
2. **Screenshots** of the 1-3 screens that matter (a real screenshot beats any mockup).
3. **Brand colors and font** — or "استخرجها من الموقع/الشعار".
4. **Call to action and where it leads**: store link, website, "حمّله من آب ستور", "سجّل مجانًا".
5. **Facts you may state**: numbers, what is free, awards. Nothing else gets claimed. No prices unless they insist (they differ by country and change).
6. **Music**: bundled upbeat bed (default) / calm / none.
7. **3D shots** (only offer if `doctor.sh` found Blender): "لقطات ثلاثية الأبعاد (شعار مجسّم، عناصر تطير) — تضيف 10-20 دقيقة".

## The requirements checklist — show it, then wait

Before building, post one compact table and ask for a go:

| البند | الحالة |
|---|---|
| الهدف والمنصة والمدة | ✅ إعلان إطلاق · عمودي · 25 ث |
| المصدر | ✅ المشروع في المجلد |
| الشعار / الصور | ✅ من المشروع · ⏳ أرسل لقطة شاشة الدفع |
| الصوت | ⏳ مفتاح Gemini — سأفتح لك ملفًا لتلصقه |
| الموسيقى | ✅ المرفقة |
| ما يُذكر من أرقام | ✅ «٣٤ درسًا»، «مجانًا» فقط |

Then set up whatever is ⏳ (key file via `key_setup.sh`, asking for the missing file) and
start only when every required row is ✅ or the user accepts a fallback (edge-tts instead of
a key, a designed mockup instead of a screenshot).

## Getting files from a non-technical user

- **Files**: "اسحب الملف إلى نافذة المحادثة" works in the Claude app and terminal. Or ask them
  to put files in a folder named `assets-in/` inside the project folder and tell you when done.
- **Links**: fetch the page yourself (WebFetch, or the browser tool for screenshots). Ask
  before logging in anywhere; never type their passwords.
- **Keys**: always through `scripts/key_setup.sh` (a private file they paste into), never chat.
