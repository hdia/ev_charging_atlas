function debounce(fn, ms) {{ let t; return function(...args) {{ clearTimeout(t); t = setTimeout(() => fn.apply(this,args), ms); }}; }}
      const geoCache = new Map();
      async function nominatimSuggest(q, which) {{
        const key = which + '|' + q.trim();
        if (!q || q.length < 3) return [];
        if (geoCache.has(key)) return geoCache.get(key);
        const url = 'https://nominatim.openstreetmap.org/search?format=jsonv2&countrycodes=au&limit=5&q=' + encodeURIComponent(q);
        try {{
          const resp = await fetch(url, {{ headers: {{ 'Accept': 'application/json' }} }});
          if (!resp.ok) throw new Error('HTTP ' + resp.status);
          const data = await resp.json();

const items = data.map(d => {{
    const parts = d.display_name.split(',').map(p => p.trim());
    const filtered = parts.filter(p => !/Australia/i.test(p) && !/^\d{{4}}$/.test(p));
    const label = filtered.slice(0, 3).join(', ');
    return {{
        label: label,
        lat: parseFloat(d.lat),
        lon: parseFloat(d.lon)
    }};
}});

// Deduplicate by label (keep first occurrence)
const unique = [];
const seen = new Set();
for (const it of items) {{
    if (!seen.has(it.label)) {{
        seen.add(it.label);
        unique.push(it);
    }}
}}

geoCache.set(key, unique);
return unique;