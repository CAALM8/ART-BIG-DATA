import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Museum Explorer", layout="wide")

st.title("🏛️ Museum Explorer")
st.markdown("从 GitHub 上读取博物馆数据（静态 JSON），并在 Streamlit 中展示。")

# --- 配置：把下面 URL 替换为你的 raw GitHub JSON 文件 URL ---
# 示例格式:
# https://raw.githubusercontent.com/<GITHUB_USER>/<REPO_NAME>/<BRANCH>/data/museum.json
RAW_JSON_URL = st.text_input("GitHub raw JSON URL", value="https://raw.githubusercontent.com/<USER>/<REPO>/main/data/museum.json")

@st.cache_data(ttl=600)
def load_data(url):
    try:
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"无法读取 JSON：{e}")
        return None

data = load_data(RAW_JSON_URL)
if not data:
    st.stop()

museum = data.get("museum", {})
st.subheader(museum.get("name", "—"))
st.write(museum.get("description", ""))

records = []
for coll in museum.get("collections", []):
    coll_id = coll.get("id")
    coll_title = coll.get("title")
    coll_cat = coll.get("category")
    for item in coll.get("items", []):
        records.append({
            "collection_id": coll_id,
            "collection": coll_title,
            "category": coll_cat,
            "item_id": item.get("id"),
            "title": item.get("title"),
            "artist": item.get("artist"),
            "year": item.get("year"),
            "description": item.get("description"),
            "image_url": item.get("image_url", "")
        })

df = pd.DataFrame(records)

# 左侧过滤区
with st.sidebar:
    st.header("筛选器")
    category_choices = ["全部"] + sorted(list({r["category"] for r in records if r["category"]}))
    chosen_cat = st.selectbox("按藏品分类", category_choices, index=0)
    search = st.text_input("搜索标题 / 艺术家 / 描述")
    min_year = st.text_input("起始年份（可空）")
    max_year = st.text_input("结束年份（可空）")

# 应用过滤
filtered = df.copy()
if chosen_cat != "全部":
    filtered = filtered[filtered["category"] == chosen_cat]
if search:
    mask = filtered.apply(lambda row: search.lower() in str(row["title"]).lower() or \
                                     search.lower() in str(row["artist"]).lower() or \
                                     search.lower() in str(row["description"]).lower(), axis=1)
    filtered = filtered[mask]

def parse_year(y):
    try:
        return int(str(y)[:4])
    except:
        return None

if min_year:
    try:
        min_y = int(min_year)
        filtered = filtered[filtered["year"].apply(lambda y: (parse_year(y) or 0) >= min_y)]
    except:
        pass
if max_year:
    try:
        max_y = int(max_year)
        filtered = filtered[filtered["year"].apply(lambda y: (parse_year(y) or 9999) <= max_y)]
    except:
        pass

st.write(f"共找到 **{len(filtered)}** 件藏品。")

if len(filtered) == 0:
    st.info("无符合条件的藏品。")
else:
    st.dataframe(filtered[["collection", "title", "artist", "year", "category"]].reset_index(drop=True))

    idx = st.number_input("选择结果编号（从 0 开始）查看详情", min_value=0, max_value=max(0, len(filtered)-1), value=0)
    item = filtered.reset_index(drop=True).iloc[int(idx)].to_dict()
    st.subheader(item["title"])
    st.markdown(f"**艺术家**：{item.get('artist','-')}  \n**年代**：{item.get('year','-')}  \n**藏品分类**：{item.get('category','-')}")
    st.write(item.get("description","-"))
    if item.get("image_url"):
        st.image(item["image_url"], use_column_width=True)
    else:
        st.info("该藏品无图片或 image_url 为空。")

st.markdown("---")
col1, col2 = st.columns([1,3])
with col1:
    st.download_button("下载 当前筛选 JSON", data=filtered.to_json(orient="records", force_ascii=False, indent=2), file_name="museum_filtered.json")
with col2:
    st.write("提示：把 `data/museum.json` 放到你的 GitHub 仓库并使用 raw.githubusercontent.com 的 URL 填入上方输入框，Streamlit 程序就能读取数据。")
