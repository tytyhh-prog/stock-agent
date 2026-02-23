import yfinance as yf
import anthropic
import smtplib
from email.mime.text import MIMEText
import os

def get_candidates():
    tickers = [
        "AAPL","MSFT","GOOGL","META","AMZN",
        "NVDA","AMD","TSLA","NFLX","CRM",
        "ADBE","INTC","QCOM","TXN","AVGO"
    ]
    candidates = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            pe = info.get("trailingPE", 999)
            growth = info.get("revenueGrowth", 0)
            roe = info.get("returnOnEquity", 0)
            price = info.get("currentPrice", 0)
            name = info.get("shortName", ticker)
            if pe and pe < 30 and growth and growth > 0.1:
                candidates.append({
                    "ticker": ticker,
                    "name": name,
                    "pe": round(pe, 2),
                    "growth": round(growth * 100, 1),
                    "roe": round((roe or 0) * 100, 1),
                    "price": price
                })
        except:
            continue
    return candidates

def analyze_with_claude(candidates):
    client = anthropic.Anthropic(api_key=os.environ["CLAUDE_API_KEY"])
    candidate_text = "\n".join([
        f"{c['ticker']} ({c['name']}): PER={c['pe']}, 매출성장률={c['growth']}%, ROE={c['roe']}%, 현재가=${c['price']}"
        for c in candidates
    ])
    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1500,
        messages=[{
            "role": "user",
            "content": f"""다음 종목들 중 오늘 가장 추천할 1종목을 골라주세요.

기준:
1. 저평가 (낮은 PER)
2. 성장성 (높은 매출성장률)
3. 수익성 (높은 ROE)
4. 미래전망 (AI 대체 위험도, 경쟁 해자, 산업 트렌드)

후보 종목:
{candidate_text}

다음 형식으로 답해주세요:
🏆 오늘의 추천 종목: [티커] ([회사명])
💰 현재가: $[가격]
📊 핵심 지표: PER [수치], 매출성장률 [수치]%, ROE [수치]%
🔮 미래 전망: AI 대체 위험도 [낮음/중간/높음] - [이유 1줄]
🏰 경쟁 해자: [핵심 경쟁우위 1줄]
✅ 추천 이유: [3줄 이내]
⚠️ 리스크: [1줄]
* 이 분석은 참고용이며 투자 판단은 본인 책임입니다."""
        }]
    )
    return message.content[0].text

def send_email(result):
    sender = os.environ["EMAIL"]
    password = os.environ["EMAIL_PASSWORD"]
    msg = MIMEText(result, 'plain', 'utf-8')
    msg['Subject'] = '📈 오늘의 주식 추천'
    msg['From'] = sender
    msg['To'] = sender
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(sender, password)
        smtp.send_message(msg)

if __name__ == "__main__":
    print("후보 종목 수집 중...")
    candidates = get_candidates()
    print(f"{len(candidates)}개 후보 발견")
    print("Claude 분석 중...")
    result = analyze_with_claude(candidates)
    print(result)
    print("이메일 발송 중...")
    send_email(result)
    print("완료!")
