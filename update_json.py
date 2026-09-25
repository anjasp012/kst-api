import psycopg2

conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/kst_db")
cur = conn.cursor()

cur.execute("SELECT id, riset FROM kst_locations")
rows = cur.fetchall()

for row in rows:
    id = row[0]
    riset_arr = row[1]
    if riset_arr:
        new_riset_arr = []
        for item in riset_arr:
            if 'bidang' in item:
                item['tema'] = item.pop('bidang')
            new_riset_arr.append(item)
        import json
        cur.execute("UPDATE kst_locations SET riset = %s WHERE id = %s", (json.dumps(new_riset_arr), id))

conn.commit()
cur.close()
conn.close()
