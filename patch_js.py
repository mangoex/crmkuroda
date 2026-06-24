with open("static/app.js", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("global_sales_target: state.global_sales_target || 0,", "")
content = content.replace('global_goals: state.global_goals || "",', "")

with open("static/app.js", "w", encoding="utf-8") as f:
    f.write(content)
