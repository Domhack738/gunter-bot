async def add_tokens(user_id: int, amount: float, session):
    user = await session.get(User, user_id)
    user.balance_token += amount
    await session.commit()
    return user.balance_token

# Проверка перед Airdrop (холдирование)
async def hold_for_airdrop(session):
    all_users = await session.execute(select(User))
    snapshot = {user.tg_id: user.balance_token for user in all_users.scalars()}
    # Отправляем в CSV для будущего Airdrop
    return snapshot