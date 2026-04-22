import psycopg2

def transfer_balance(from_user_id: int, to_user_id: int, amount: float, conn):
    cursor = conn.cursor()

    # Check sender balance
    cursor.execute("SELECT balance FROM users WHERE id = %s", (from_user_id,))
    sender = cursor.fetchone()

    if sender["balance"] < amount:
        raise ValueError("Insufficient funds")

    # Deduct from sender
    cursor.execute(
        "UPDATE users SET balance = balance - %s WHERE id = %s",
        (amount, from_user_id)
    )

    # Add to receiver
    cursor.execute(
        "UPDATE users SET balance = balance + %s WHERE id = %s",
        (amount, to_user_id)
    )

    conn.commit()
    cursor.close()
