import markdown

with open('USER_MANUAL.md', 'r', encoding='utf-8') as f:
    md_text = f.read()

html_body = markdown.markdown(md_text, extensions=['fenced_code', 'tables'])

html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AutoCheckout Hub - User Manual</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 900px; margin: 0 auto; padding: 40px 20px; background-color: #f4f7f6; }
        .container { background: #fff; padding: 50px; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); }
        h1 { font-size: 2.5em; color: #111827; border-bottom: 3px solid #6366f1; padding-bottom: 12px; margin-bottom: 24px; font-weight: 800; }
        h2 { font-size: 1.8em; color: #1f2937; border-bottom: 1px solid #e5e7eb; padding-bottom: 10px; margin-top: 48px; font-weight: 700; }
        h3 { font-size: 1.4em; color: #374151; margin-top: 32px; font-weight: 600; }
        p { margin-bottom: 18px; font-size: 1.1em; color: #4b5563; }
        code { background-color: #f3f4f6; padding: 3px 6px; border-radius: 6px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; font-size: 0.9em; color: #ef4444; font-weight: 600; }
        pre { background-color: #1f2937; color: #f9fafb; padding: 20px; border-radius: 12px; overflow-x: auto; box-shadow: inset 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 24px; }
        pre code { background-color: transparent; padding: 0; color: inherit; font-weight: normal; }
        a { color: #6366f1; text-decoration: none; font-weight: 500; }
        a:hover { text-decoration: underline; color: #4f46e5; }
        ul, ol { padding-left: 24px; margin-bottom: 20px; color: #4b5563; }
        li { margin-bottom: 10px; font-size: 1.1em; }
        hr { border: 0; border-top: 1px solid #e5e7eb; margin: 48px 0; }
        strong { color: #111827; }
        em { color: #6b7280; font-style: italic; }
    </style>
</head>
<body>
    <div class="container">
        {html_body}
    </div>
</body>
</html>"""

with open('USER_MANUAL.html', 'w', encoding='utf-8') as f:
    f.write(html_template.replace('{html_body}', html_body))
