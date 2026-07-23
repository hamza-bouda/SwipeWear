import { NextResponse } from "next/server";
import { Pool } from "pg";
import { randomBytes } from "crypto";

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 5,
});

async function ensureTable() {
  await pool.query(`
    CREATE TABLE IF NOT EXISTS waitlist (
      id SERIAL PRIMARY KEY,
      email TEXT UNIQUE NOT NULL,
      utm_source TEXT,
      utm_medium TEXT,
      utm_campaign TEXT,
      utm_content TEXT,
      confirmed BOOLEAN NOT NULL DEFAULT FALSE,
      confirmation_token TEXT UNIQUE,
      created_at TIMESTAMPTZ DEFAULT NOW()
    )
  `);
  // Idempotent: add columns if the table already existed without them
  await pool.query(`
    ALTER TABLE waitlist
      ADD COLUMN IF NOT EXISTS confirmed BOOLEAN NOT NULL DEFAULT FALSE,
      ADD COLUMN IF NOT EXISTS confirmation_token TEXT
  `);
}

let tableReady = false;

async function getTable() {
  if (!tableReady) {
    await ensureTable();
    tableReady = true;
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { email, utm_source, utm_medium, utm_campaign, utm_content } = body;

    if (!email || typeof email !== "string") {
      return NextResponse.json({ error: "Email requis" }, { status: 400 });
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return NextResponse.json({ error: "Email invalide" }, { status: 400 });
    }

    await getTable();

    const token = randomBytes(32).toString("hex");
    const normalizedEmail = email.toLowerCase().trim();

    const result = await pool.query(
      `INSERT INTO waitlist (email, utm_source, utm_medium, utm_campaign, utm_content, confirmation_token)
       VALUES ($1, $2, $3, $4, $5, $6)
       ON CONFLICT (email) DO UPDATE
         SET confirmation_token = EXCLUDED.confirmation_token
       RETURNING confirmed`,
      [normalizedEmail, utm_source || null, utm_medium || null, utm_campaign || null, utm_content || null, token]
    );

    // If already confirmed, don't resend
    if (result.rows[0]?.confirmed) {
      return NextResponse.json({ success: true, alreadyConfirmed: true });
    }

    await sendConfirmationEmail(normalizedEmail, token);

    return NextResponse.json({ success: true });
  } catch (err) {
    console.error("Waitlist error:", err);
    return NextResponse.json(
      { error: "Une erreur est survenue" },
      { status: 500 }
    );
  }
}

export async function GET() {
  try {
    await getTable();
    const result = await pool.query("SELECT COUNT(*) FROM waitlist WHERE confirmed = TRUE");
    return NextResponse.json({ count: parseInt(result.rows[0].count, 10) });
  } catch {
    return NextResponse.json({ count: 0 });
  }
}

async function sendConfirmationEmail(email: string, token: string) {
  const resendApiKey = process.env.RESEND_API_KEY;
  if (!resendApiKey) {
    console.warn("RESEND_API_KEY not set — skipping confirmation email");
    return;
  }

  const baseUrl = process.env.NEXT_PUBLIC_BASE_URL || "https://swipewear.fr";
  const confirmUrl = `${baseUrl}/api/waitlist/confirm?token=${token}`;

  await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${resendApiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from: "SwipeWear <noreply@swipewear.fr>",
      to: [email],
      subject: "Confirme ton inscription — SwipeWear",
      html: buildConfirmationEmailHtml(confirmUrl),
    }),
  });
}

function buildConfirmationEmailHtml(confirmUrl: string): string {
  return `<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#fafafa;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0" style="padding:40px 20px">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:16px;border:1px solid #f0f0f0;overflow:hidden;max-width:100%">
        <tr><td style="padding:40px 40px 0">
          <p style="margin:0;font-size:22px;font-weight:900;color:#111">
            Swipe<span style="color:#EAB308">Wear</span>
          </p>
        </td></tr>
        <tr><td style="padding:32px 40px">
          <h1 style="margin:0 0 16px;font-size:24px;font-weight:800;color:#111">
            Tu y es presque !
          </h1>
          <p style="margin:0 0 24px;font-size:16px;color:#555;line-height:1.6">
            Clique sur le bouton ci-dessous pour confirmer ton adresse email et rejoindre la waitlist SwipeWear.
            Tu seras parmi les premiers à être prévenus au lancement.
          </p>
          <a href="${confirmUrl}"
             style="display:inline-block;background:#111;color:#fff;text-decoration:none;font-size:15px;font-weight:700;padding:14px 32px;border-radius:12px">
            Confirmer mon inscription
          </a>
          <p style="margin:24px 0 0;font-size:12px;color:#aaa;line-height:1.6">
            Si tu n'as pas demandé cette inscription, ignore cet email.<br>
            Lien valide 7 jours. Pas de spam, juste un email au lancement.
          </p>
        </td></tr>
        <tr><td style="padding:24px 40px;border-top:1px solid #f0f0f0">
          <p style="margin:0;font-size:12px;color:#bbb">
            © ${new Date().getFullYear()} SwipeWear — Fait avec passion à Paris
          </p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>`;
}
