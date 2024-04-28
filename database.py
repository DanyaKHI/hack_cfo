import sqlite3

import aiosqlite
import asyncio

lock_lite = asyncio.Lock()


async def lock_request(request: str, args, is_commit=False):
    async with lock_lite:
        try:
            async with aiosqlite.connect('answers.db') as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(request, args) as cursor:
                    row = await cursor.fetchone()
                    if is_commit:
                        await db.commit()
                    return row
        except Exception as e:
            print(f"Database error: {e}")
            return None


async def get_answer_by_id(id_value: int):
    row = await lock_request(request='SELECT * FROM answers WHERE id = ?',
                             args=(id_value,))
    if row is not None:
        return row['answer']
    else:
        return None


async def get_exitsting_user(user_id: int):
    row = await lock_request(request='SELECT * from users WHERE id=?',
                             args=(user_id,))


async def add_user(user_id: int, username: str):
    return await lock_request(request='INSERT INTO users(id, username) VALUES(?, ?)',
                              args=(user_id, username),
                              is_commit=True)


async def ls_max_session(user_id: int):
    req = await lock_request(request='SELECT * FROM stories WHERE user_id=?',
                             args=(user_id, ))
    req = req['session'] + 1 if req is not None else 0
    return req


async def add_session(user_id: int, list_reqs: list):
    ls = await ls_max_session(user_id)
    for i in range(len(list_reqs)):
        await lock_request(request='INSERT INTO stories(user_id, session, message, lag) VALUES(?, ?, ?, ?)',
                           args=(user_id, ls, list_reqs[i], i),
                           is_commit=True)

