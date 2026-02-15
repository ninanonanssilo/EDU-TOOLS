export async function onRequestPost(context) {
  const { request, env } = context;

  // --- Config ---
  const TO_EMAIL = env.CONTACT_TO_EMAIL || "hongseok223@naver.com";
  const FROM_EMAIL = env.CONTACT_FROM_EMAIL || "onboarding@resend.dev";
  const SITE_NAME = env.CONTACT_SITE_NAME || "EDU TOOLS";

  if (!env.RESEND_API_KEY) {
    return json({ ok: false, error: "RESEND_API_KEY not configured" }, 500);
  }

  // --- Basic anti-spam ---
  const ip =
    request.headers.get("CF-Connecting-IP") ||
    (request.headers.get("x-forwarded-for") || "").split(",")[0].trim() ||
    "unknown";

  // rate limit: 1 request per 30s per IP (best-effort via cache)
  try {
    const key = new Request(`https://rate-limit.local/contact/${encodeURIComponent(ip)}`);
    const hit = await caches.default.match(key);
    if (hit) {
      return json({ ok: false, error: "잠시 후 다시 시도해 주세요." }, 429);
    }
    await caches.default.put(
      key,
      new Response("1", {
        headers: { "Cache-Control": "max-age=30" },
      })
    );
  } catch {
    // ignore cache failures
  }

  let data;
  try {
    data = await request.json();
  } catch {
    return json({ ok: false, error: "Invalid JSON" }, 400);
  }

  const name = clean(data?.name);
  const email = clean(data?.email);
  const message = clean(data?.message);
  const hp = clean(data?.company); // honeypot

  if (hp) return json({ ok: true }, 200); // silently accept

  if (!message || message.length < 5) {
    return json({ ok: false, error: "문의 내용을 5자 이상 입력해 주세요." }, 400);
  }
  if (message.length > 4000) {
    return json({ ok: false, error: "문의 내용이 너무 깁니다." }, 400);
  }

  if (email && !looksLikeEmail(email)) {
    return json({ ok: false, error: "이메일 형식이 올바르지 않습니다." }, 400);
  }

  const subject = `[${SITE_NAME}] 문의` + (name ? ` (${name})` : "");

  const text = [
    `사이트: ${SITE_NAME}`,
    `보낸이: ${name || "(미기재)"}`,
    `회신 이메일: ${email || "(미기재)"}`,
    `IP: ${ip}`,
    "",
    "--- 문의 내용 ---",
    message,
    "",
  ].join("\n");

  const payload = {
    from: FROM_EMAIL,
    to: [TO_EMAIL],
    subject,
    text,
    reply_to: email || undefined,
  };

  try {
    const r = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.RESEND_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!r.ok) {
      const errText = await r.text().catch(() => "");
      return json(
        {
          ok: false,
          error: "메일 전송에 실패했습니다.",
          detail: errText?.slice(0, 500) || "",
        },
        502
      );
    }

    return json({ ok: true }, 200);
  } catch {
    return json({ ok: false, error: "메일 전송에 실패했습니다." }, 502);
  }
}

function json(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
    },
  });
}

function clean(v) {
  return String(v ?? "").replace(/\r/g, "").trim();
}

function looksLikeEmail(s) {
  // practical, not perfect
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s);
}
