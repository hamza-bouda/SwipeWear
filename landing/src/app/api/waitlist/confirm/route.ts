import { NextResponse } from "next/server";
import { Pool } from "pg";

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 5,
});

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const token = searchParams.get("token");

  if (!token) {
    return NextResponse.redirect(new URL("/", request.url));
  }

  try {
    const result = await pool.query(
      `UPDATE waitlist
       SET confirmed = TRUE, confirmation_token = NULL
       WHERE confirmation_token = $1
         AND confirmed = FALSE
       RETURNING email`,
      [token]
    );

    if (result.rowCount === 0) {
      // Token not found or already confirmed
      return NextResponse.redirect(new URL("/confirme?status=already", request.url));
    }

    return NextResponse.redirect(new URL("/confirme?status=ok", request.url));
  } catch (err) {
    console.error("Confirm error:", err);
    return NextResponse.redirect(new URL("/confirme?status=error", request.url));
  }
}
