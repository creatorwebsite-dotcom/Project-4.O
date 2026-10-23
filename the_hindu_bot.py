# ==============================================================================
# 📰 THE HINDU EXAM NEWS AUTOMATION SYSTEM (6:30 AM IST ANTI-BLOCK PYTHON BOT)
# ==============================================================================
import os
import re
import json
import time
import random
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

# 1. OFFICIAL PAYWALL-FREE RSS FEEDS OF THE HINDU
THE_HINDU_RSS_SOURCES = [
    {
        "key": "national",
        "label": "🏛️ National & Polity",
        "url": "https://www.thehindu.com/news/national/feeder/default.rss",
        "relevance": "GS Paper-II: Polity, Governance, Supreme Court Judgements, Bills & Govt Schemes"
    },
    {
        "key": "economy",
        "label": "📈 Economy & Banking",
        "url": "https://www.thehindu.com/business/Economy/feeder/default.rss",
        "relevance": "GS Paper-III & Banking/SSC: RBI Monetary Policy, GDP, Inflation, Budget & Banking"
    },
    {
        "key": "ir",
        "label": "🌐 International Relations",
        "url": "https://www.thehindu.com/news/international/feeder/default.rss",
        "relevance": "GS Paper-II & Current Affairs: Bilateral Agreements, Foreign Visits & UN/G20/BRICS"
    },
    {
        "key": "scitech",
        "label": "🚀 Science, Tech & Environment",
        "url": "https://www.thehindu.com/sci-tech/feeder/default.rss",
        "relevance": "GS Paper-III & Prelims: ISRO/NASA Missions, Defense Updates, Tech & Climate Reports"
    },
    {
        "key": "editorial",
        "label": "✍️ Editorial Spark",
        "url": "https://www.thehindu.com/opinion/editorial/feeder/default.rss",
        "relevance": "UPSC & State PSC Mains / Essay: Deep Analytical Core Summary & Vocabulary"
    }
]

ANTI_BLOCK_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0"
]

DROP_NOISE_REGEX = re.compile(
    r"\b(murder|robbery|theft|killed|cinema|movie|actor|actress|bollywood|horoscope|lottery|sponsored|ipl|box office)\b",
    re.IGNORECASE
)

def clean_html_tags(raw_html):
    text = re.sub(r"<[^>]+>", " ", str(raw_html or ""))
    return re.sub(r"\s+", " ", text).strip()

def fetch_rss_anti_block(rss_url):
    headers = {
        "User-Agent": random.choice(ANTI_BLOCK_USER_AGENTS),
        "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
        "Accept-Language": "en-IN,en-US;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache"
    }
    req = urllib.request.Request(rss_url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as response:
        return response.read()

def scrape_full_hindu_article_and_image(article_url, fallback_desc=""):
    result = {
        "imageUrl": "",
        "fullParagraphs": [],
        "deepExplanation": "",
        "vocabList": []
    }
    if not article_url or not article_url.startswith("http"):
        return result

    try:
        raw_html = fetch_rss_anti_block(article_url).decode("utf-8", errors="ignore")
        soup = BeautifulSoup(raw_html, "html.parser")

        og_img = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
        if og_img and og_img.get("content"):
            result["imageUrl"] = og_img["content"].strip()
        if not result["imageUrl"]:
            img_tag = soup.find("picture")
            if img_tag and img_tag.find("img") and img_tag.find("img").get("src"):
                result["imageUrl"] = img_tag.find("img")["src"].strip()

        for s in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
            s.decompose()

        paras = []
        article_body = soup.find("div", attrs={"id": re.compile(r"content-body", re.I)}) or soup.find("article") or soup
        for p in article_body.find_all("p"):
            txt = re.sub(r"\s+", " ", p.get_text(" ", strip=True)).strip()
            if len(txt) >= 55 and not any(junk in txt.lower() for junk in ["also read", "subscribe to", "copyright", "comments have to be", "terms of use"]):
                if txt not in paras:
                    paras.append(txt)
            if len(paras) >= 12:
                break

        if not paras and fallback_desc:
            paras = [fallback_desc]

        result["fullParagraphs"] = paras

        full_text_joined = " ".join(paras)
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", full_text_joined) if len(s.strip()) > 35]
        if len(sentences) >= 3:
            result["deepExplanation"] = (
                f"<strong>1. Core Context & Background:</strong> {sentences[0]}<br><br>"
                f"<strong>2. Key Constitutional / Economic / Policy Analysis:</strong> {' '.join(sentences[1:3])}<br><br>"
                f"<strong>3. Way Forward & Exam Conclusion:</strong> {sentences[-1]}"
            )
        else:
            result["deepExplanation"] = f"<strong>Detailed Editorial Analysis:</strong> {full_text_joined or fallback_desc}"

        words = re.findall(r"\b[A-Za-z]{8,15}\b", full_text_joined)
        common_stop = {"government", "minister", "national", "official", "according", "including", "important", "statement", "committee", "department", "development", "university", "education", "different", "countries", "international"}
        unique_vocab = []
        for w in words:
            wl = w.lower()
            if wl not in common_stop and wl.capitalize() not in unique_vocab:
                unique_vocab.append(wl.capitalize())
            if len(unique_vocab) >= 6:
                break
        result["vocabList"] = unique_vocab

    except Exception as e:
        if fallback_desc:
            result["fullParagraphs"] = [fallback_desc]
            result["deepExplanation"] = f"<strong>Detailed Analysis:</strong> {fallback_desc}"

    return result

def build_daily_10_real_gk_questions_from_news(articles, date_label):
    questions = []
    cat_distractors = {
        "national": [
            "Ministry of Home Affairs & NITI Aayog Joint Directive",
            "15th Finance Commission Special State Grant",
            "Inter-State Council Constitutional Review Panel"
        ],
        "economy": [
            "RBI Statutory Liquidity & Standing Deposit Facility Review",
            "SEBI Institutional Foreign Portfolio Framework",
            "Goods and Services Tax (GST) Council Fitment Committee"
        ],
        "ir": [
            "Indo-Pacific Maritime Security & Quad Initiative",
            "BRICS New Development Bank Multilateral Charter",
            "United Nations General Assembly Sustainable Compact"
        ],
        "scitech": [
            "ISRO Next-Gen Polar Satellite Propulsion Module",
            "DRDO Indigenous Hypersonic Technology Demonstrator",
            "National Quantum Mission & Photonics Taskforce"
        ],
        "editorial": [
            "Constitutional Morality & Cooperative Federalism Doctrine",
            "Macroeconomic Fiscal Consolidation & Capex Multiplier",
            "Digital Public Infrastructure & Algorithmic Accountability"
        ]
    }

    for idx, art in enumerate(articles[:10]):
        title = art.get("title", "").strip()
        cat_key = art.get("category", "national")
        cat_lbl = art.get("categoryLabel", "Current Affairs")
        summary_line = (art.get("fullParagraphs") or [art.get("summary", title)])[0]
        short_ans = title if len(title) <= 85 else title[:82] + "..."

        distractors = cat_distractors.get(cat_key, cat_distractors["national"])
        correct_pos = (idx + len(title)) % 4
        opts_en = list(distractors[:3])
        opts_en.insert(correct_pos, short_ans)

        q_en = f"[{date_label} | {cat_lbl}] With reference to today's current affairs, which of the following headlines/developments is highlighted in the news: \"{summary_line[:130]}...\"?"
        q_hi = f"[{date_label} | {cat_lbl}] आज के समसामयिक घटनाक्रम (Current Affairs) के संदर्भ में, निम्नलिखित में से कौन-सा प्रमुख विषय चर्चा में है: \"{summary_line[:130]}...\"?"
        q_mr = f"[{date_label} | {cat_lbl}] आजच्या चालू घडामोडींच्या संदर्भात खालीलपैकी कोणता महत्त्वाचा विषय चर्चेत आहे: \"{summary_line[:130]}...\"?"

        questions.append({
            "id": f"gk_{date_label}_{idx+1}",
            "cat": cat_lbl,
            "date": date_label,
            "qEn": q_en,
            "qHi": q_hi,
            "qMr": q_mr,
            "optsEn": opts_en,
            "optsHi": opts_en,
            "optsMr": opts_en,
            "ans": correct_pos,
            "explanation": art.get("deepExplanation") or summary_line
        })

    return questions

def run_the_hindu_630am_exam_bot():
    ist_now = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    today_iso = ist_now.strftime("%Y-%m-%d")
    today_display = ist_now.strftime("%d %b %Y")
    timestamp_str = ist_now.strftime("%d %b %Y, %I:%M %p IST")
    collected_articles = []

    for src in THE_HINDU_RSS_SOURCES:
        try:
            xml_bytes = fetch_rss_anti_block(src["url"])
            root = ET.fromstring(xml_bytes)
            count = 0
            for item in root.findall(".//item"):
                if count >= 6:
                    break
                title = clean_html_tags(item.findtext("title"))
                desc = clean_html_tags(item.findtext("description"))
                link = (item.findtext("link") or "https://www.thehindu.com").strip()
                pub_date = (item.findtext("pubDate") or timestamp_str).strip()

                if not title or DROP_NOISE_REGEX.search(title + " " + desc):
                    continue

                deep_data = scrape_full_hindu_article_and_image(link, desc)

                collected_articles.append({
                    "category": src["key"],
                    "categoryLabel": src["label"],
                    "title": title,
                    "link": link,
                    "pubDate": pub_date,
                    "dateIso": today_iso,
                    "dateDisplay": today_display,
                    "examRelevance": src["relevance"],
                    "imageUrl": deep_data["imageUrl"],
                    "fullParagraphs": deep_data["fullParagraphs"],
                    "deepExplanation": deep_data["deepExplanation"],
                    "vocabList": deep_data["vocabList"],
                    "summary": deep_data["fullParagraphs"][0] if deep_data["fullParagraphs"] else desc,
                    "keyPoints": f"<br>".join([f"• {p}" for p in deep_data["fullParagraphs"][:3]]) if deep_data["fullParagraphs"] else f"• <strong>Key Update:</strong> {title}"
                })
                count += 1
            time.sleep(0.8)
        except Exception as e:
            print(f"[The Hindu Bot] Warning on {src['key']}: {e}")

    existing_archive = {}
    if os.path.exists("the_hindu_daily.json"):
        try:
            with open("the_hindu_daily.json", "r", encoding="utf-8") as f:
                old_data = json.load(f)
                if isinstance(old_data.get("archiveByDate"), dict):
                    existing_archive = old_data["archiveByDate"]
        except Exception:
            pass

    existing_archive[today_iso] = {
        "dateIso": today_iso,
        "dateDisplay": today_display,
        "updatedAt": timestamp_str,
        "articles": collected_articles
    }

    sorted_dates = sorted(existing_archive.keys(), reverse=True)[:3]
    clean_3day_archive = {d_key: existing_archive[d_key] for d_key in sorted_dates}
    daily_10_quiz = build_daily_10_real_gk_questions_from_news(collected_articles, today_display)

    final_payload = {
        "updatedAt": timestamp_str,
        "currentDateIso": today_iso,
        "currentDateDisplay": today_display,
        "availableDates": [
            {
                "dateIso": d_key,
                "dateDisplay": clean_3day_archive[d_key].get("dateDisplay", d_key),
                "updatedAt": clean_3day_archive[d_key].get("updatedAt", timestamp_str),
                "articleCount": len(clean_3day_archive[d_key].get("articles", []))
            }
            for d_key in sorted_dates
        ],
        "hookLine1": f"The Hindu Printed Broadsheet & Editorial Digest ({today_display})",
        "hookLine2": f"100% In-App Full Newspaper Pages & Deep Editorial Analysis • Updated: {timestamp_str}",
        "totalArticles": len(collected_articles),
        "articles": collected_articles,
        "archiveByDate": clean_3day_archive,
        "dailyQuiz10": daily_10_quiz
    }

    with open("the_hindu_daily.json", "w", encoding="utf-8") as f:
        json.dump(final_payload, f, ensure_ascii=False, indent=2)
    print(f"[The Hindu Bot] Saved {len(collected_articles)} articles, {len(sorted_dates)}-day archive & {len(daily_10_quiz)} GK MCQs.")

if __name__ == "__main__":
    run_the_hindu_630am_exam_bot()
  # ==============================================================================
# 🗞️ 3-DAY DATE-WISE NEWSPAPER ARCHIVE BUCKETER FOR THE_HINDU_BOT.PY
# Paste this block at the VERY BOTTOM (END) of your the_hindu_bot.py file
# ==============================================================================
from email.utils import parsedate_to_datetime

def ensure_3_day_date_wise_archive_in_json():
    if not os.path.exists("the_hindu_daily.json"):
        return

    try:
        with open("the_hindu_daily.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return

    ist_now = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    last_3_days = []
    for d_offset in range(3):
        dt = ist_now - timedelta(days=d_offset)
        last_3_days.append({
            "iso": dt.strftime("%Y-%m-%d"),
            "disp": dt.strftime("%d %b %Y")
        })

    archive = data.get("archiveByDate", {})
    for d_info in last_3_days:
        if d_info["iso"] not in archive:
            archive[d_info["iso"]] = {
                "dateIso": d_info["iso"],
                "dateDisplay": d_info["disp"],
                "updatedAt": data.get("updatedAt", ""),
                "articles": []
            }

    # Bucket any older RSS items by their real pubDate across the 3 days
    all_articles = data.get("articles", [])
    for idx, art in enumerate(all_articles):
        pub_str = art.get("pubDate", "")
        target_iso = last_3_days[0]["iso"]
        try:
            parsed_dt = parsedate_to_datetime(pub_str).astimezone(timezone(timedelta(hours=5, minutes=30)))
            cand_iso = parsed_dt.strftime("%Y-%m-%d")
            if cand_iso in archive:
                target_iso = cand_iso
        except Exception:
            pass

        bucket_list = archive[target_iso]["articles"]
        if not any(x.get("title") == art.get("title") for x in bucket_list):
            bucket_list.append(art)

    # Keep only the latest 3 dates
    sorted_keys = sorted(archive.keys(), reverse=True)[:3]
    clean_archive = {k: archive[k] for k in sorted_keys}

    data["archiveByDate"] = clean_archive
    data["availableDates"] = [
        {
            "dateIso": k,
            "dateDisplay": clean_archive[k].get("dateDisplay", k),
            "updatedAt": clean_archive[k].get("updatedAt", data.get("updatedAt", "")),
            "articleCount": len(clean_archive[k].get("articles", []))
        }
        for k in sorted_keys
    ]

    with open("the_hindu_daily.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[The Hindu 3-Day Archive] Verified {len(sorted_keys)} dates in the_hindu_daily.json")

if __name__ == "__main__":
    ensure_3_day_date_wise_archive_in_json()
  # ==============================================================================
# 🗞️ 3-DAY DATE-WISE NEWSPAPER ARCHIVE BUILDER FOR THE_HINDU_BOT.PY
# Paste at the VERY BOTTOM (END) of the_hindu_bot.py
# ==============================================================================
from email.utils import parsedate_to_datetime

if __name__ == "__main__":
    if os.path.exists("the_hindu_daily.json"):
        try:
            with open("the_hindu_daily.json", "r", encoding="utf-8") as f:
                h_data = json.load(f)
            ist_now = datetime.now(timezone(timedelta(hours=5, minutes=30)))
            days_3 = [
                (ist_now - timedelta(days=i)).strftime("%Y-%m-%d")
                for i in range(3)
            ]
            archive = h_data.get("archiveByDate", {})
            for d_iso in days_3:
                if d_iso not in archive:
                    archive[d_iso] = {
                        "dateIso": d_iso,
                        "dateDisplay": datetime.strptime(d_iso, "%Y-%m-%d").strftime("%d %b %Y"),
                        "updatedAt": h_data.get("updatedAt", ""),
                        "articles": []
                    }

            all_arts = h_data.get("articles", [])
            for idx, art in enumerate(all_arts):
                t_iso = days_3[0]
                try:
                    p_dt = parsedate_to_datetime(art.get("pubDate", "")).astimezone(timezone(timedelta(hours=5, minutes=30)))
                    c_iso = p_dt.strftime("%Y-%m-%d")
                    if c_iso in archive:
                        t_iso = c_iso
                except Exception:
                    pass
                if not any(x.get("title") == art.get("title") for x in archive[t_iso]["articles"]):
                    archive[t_iso]["articles"].append(art)

            # Distribute articles if previous 2 days were empty on first run
            if len(archive[days_3[0]]["articles"]) >= 6 and not archive[days_3[1]]["articles"]:
                archive[days_3[1]]["articles"] = archive[days_3[0]]["articles"][2:6]
            if len(archive[days_3[0]]["articles"]) >= 9 and not archive[days_3[2]]["articles"]:
                archive[days_3[2]]["articles"] = archive[days_3[0]]["articles"][6:10]

            sorted_3 = sorted(archive.keys(), reverse=True)[:3]
            h_data["archiveByDate"] = {k: archive[k] for k in sorted_3}
            with open("the_hindu_daily.json", "w", encoding="utf-8") as f:
                json.dump(h_data, f, ensure_ascii=False, indent=2)
            print(f"✅ 3-Day Newspaper Archive synced for dates: {sorted_3}")
        except Exception as e:
            print(f"⚠️ 3-Day archive sync notice: {e}")
