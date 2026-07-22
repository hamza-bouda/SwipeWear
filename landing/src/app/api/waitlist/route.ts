import { NextResponse } from "next/server";
import { Pool } from "pg";

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
      created_at TIMESTAMPTZ DEFAULT NOW()
    )
  `);
}

let tableReady = false;

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

    if (!tableReady) {
      await ensureTable();
      tableReady = true;
    }

    await pool.query(
      `INSERT INTO waitlist (email, utm_source, utm_medium, utm_campaign, utm_content)
       VALUES ($1, $2, $3, $4, $5)
       ON CONFLICT (email) DO NOTHING`,
      [
        email.toLowerCase().trim(),
        utm_source || null,
        utm_medium || null,
        utm_campaign || null,
        utm_content || null,
      ]
    );

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
    if (!tableReady) {
      await ensureTable();
      tableReady = true;
    }

    const result = await pool.query("SELECT COUNT(*) FROM waitlist");
    return NextResponse.json({ count: parseInt(result.rows[0].count, 10) });
  } catch {
    return NextResponse.json({ count: 0 });
  }
}
