import os


print(os.environ.get("NOTION_TOKEN"), flush=True)
print(os.getenv("NOTION_DATABASE_ID"), flush=True)
