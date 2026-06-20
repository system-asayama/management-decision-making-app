# -*- coding: utf-8 -*-
"""
セキュリティ関連ヘルパー
"""

import secrets
from typing import Optional
from flask import session
from .db import get_db, _sql


def login_user(user_id: int, name: str, role: str, tenant_id: Optional[int], is_employee: bool = False):
    """ユーザーをセッションにログインさせる"""
    session.clear()
    session["user_id"] = user_id
    session["user_name"] = name
    session["role"] = role
    session["tenant_id"] = tenant_id  # system_admin は None 可
    session["is_employee"] = bool(is_employee)


def admin_exists() -> bool:
    """管理者が1人でも居れば True。

    認証用の get_db() は PostgreSQL 接続に失敗すると SQLite(database/login_auth.db)
    へフォールバックすることがあり、その SQLite には T_管理者 が無いため
    『no such table: T_管理者』で500になる。
    ここは業務DBと同じ SQLAlchemy エンジン（DATABASE_URL）を直接参照し、
    フォールバックに振り回されず常に本来のDBを見るようにする。
    """
    # 1) まず SQLAlchemy エンジン（DATABASE_URL = 本来のDB）で確認
    try:
        from app.db import engine
        from sqlalchemy import text
        with engine.connect() as econn:
            row = econn.execute(text('SELECT COUNT(*) FROM "T_管理者"')).fetchone()
            return bool(row and row[0] and int(row[0]) > 0)
    except Exception:
        pass

    # 2) フォールバック：従来の get_db()（テーブルが無ければ False 扱い）
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(_sql(conn, 'SELECT COUNT(*) FROM "T_管理者"'))
        row = cur.fetchone()
        return bool(row and row[0] and int(row[0]) > 0)
    except Exception:
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _ensure_csrf_token() -> str:
    """CSRF トークンをセッションに確保して返す"""
    tok = session.get("csrf_token")
    if not tok:
        tok = secrets.token_hex(16)
        session["csrf_token"] = tok
    return tok


def get_csrf():
    """テンプレート用のCSRFトークン取得関数"""
    return _ensure_csrf_token()


def is_owner() -> bool:
    """
    現在ログイン中のユーザーがオーナーシステム管理者かどうかを確認
    """
    user_id = session.get('user_id')
    role = session.get('role')
    
    if not user_id or role != 'system_admin':
        return False
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute(_sql(conn, 'SELECT is_owner FROM "T_管理者" WHERE id = %s'), (user_id,))
    row = cur.fetchone()
    conn.close()
    
    if row:
        return row[0] == 1
    return False


def can_manage_system_admins() -> bool:
    """
    現在ログイン中のユーザーがシステム管理者管理権限を持っているかを確認
    オーナーは常にTrue、それ以外はcan_manage_adminsフラグで判定
    """
    user_id = session.get('user_id')
    role = session.get('role')
    
    if not user_id or role != 'system_admin':
        return False
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute(_sql(conn, 'SELECT is_owner, can_manage_admins FROM "T_管理者" WHERE id = %s'), (user_id,))
    row = cur.fetchone()
    conn.close()
    
    if row:
        # オーナーは常にTrue、それ以外はcan_manage_adminsで判定
        return row[0] == 1 or row[1] == 1
    return False


def is_tenant_owner() -> bool:
    """
    現在ログイン中のユーザーがテナントオーナーかどうかを確認
    """
    user_id = session.get('user_id')
    role = session.get('role')
    
    if not user_id or role != 'tenant_admin':
        return False
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute(_sql(conn, 'SELECT is_owner FROM "T_管理者" WHERE id = %s'), (user_id,))
    row = cur.fetchone()
    conn.close()
    
    if row:
        return row[0] == 1
    return False


def can_manage_tenant_admins() -> bool:
    """
    現在ログイン中のテナント管理者が管理者管理権限を持っているかを確認
    オーナーは常にTrue、それ以外はcan_manage_adminsフラグで判定
    システム管理者は常にTrue
    """
    user_id = session.get('user_id')
    role = session.get('role')
    
    # システム管理者は常に権限あり
    if role == 'system_admin':
        return True
    
    if not user_id or role != 'tenant_admin':
        return False
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute(_sql(conn, 'SELECT is_owner, can_manage_admins FROM "T_管理者" WHERE id = %s'), (user_id,))
    row = cur.fetchone()
    conn.close()
    
    if row:
        # オーナーは常にTrue、それ以外はcan_manage_adminsで判定
        return row[0] == 1 or row[1] == 1
    return False
