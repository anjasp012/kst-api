with open("app/models/kst.py", "r") as f:
    text = f.read()

text = text.replace("from sqlalchemy import Column, ForeignKey\nfrom sqlalchemy.orm import relationship, String, Integer, Float, Text, Boolean, DateTime, JSON", "from sqlalchemy import Column, ForeignKey, String, Integer, Float, Text, Boolean, DateTime, JSON\nfrom sqlalchemy.orm import relationship")

with open("app/models/kst.py", "w") as f:
    f.write(text)
