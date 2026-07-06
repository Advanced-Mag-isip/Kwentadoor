function getBase(): string {
    return import.meta.env.PUBLIC_API_URL || 'https://accounting-api.advancedthinkers.app/api';
}

export async function get(path: string, token?: string) {
    const res = await fetch(`${getBase()}${path}`, {
        headers: token ? { Authorization: `Token ${token}` } : {}
    });
    if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
    return res.json();
}

export async function post(path: string, body: unknown, token?: string) {
    const res = await fetch(`${getBase()}${path}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Token ${token}` } : {})
        },
        body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`POST ${path} failed: ${res.status}`);
    return res.json();
}

export async function del(path: string, token?: string) {
    const res = await fetch(`${getBase()}${path}`, {
        method: 'DELETE',
        headers: token ? { Authorization: `Token ${token}` } : {}
    });
    if (!res.ok) throw new Error(`DELETE ${path} failed: ${res.status}`);
    return res.json();
}