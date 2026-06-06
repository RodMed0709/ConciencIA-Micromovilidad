# Integración con Lovable — drop-in

Este folder conecta el frontend de **Lovable** (landing + login) con los mapas
que ya están hechos (HTML autónomos con MapLibre + ruteo OpenRouteService).

La idea es simple: **Lovable maneja landing/login; al entrar, manda al usuario al
HTML del mapa.** No hay que reescribir el mapa en React.

> No existe una "API key de Lovable" para inyectar esto. Lovable se integra **vía
> GitHub** (sync bidireccional). El puente es: estos archivos viven en el `public/`
> del repo de Lovable, y Lovable los sirve estáticos.

---

## Qué hay aquí

```
lovable_bundle/
  public/
    ruta_segurav2.html      <- DEMO PRINCIPAL (ruta segura con motor de riesgo)
    mapa_riesgo.html        <- mapa de burbujas de riesgo (exploración)
    ruta_key.example.js     <- plantilla para tu API key de ORS
  INTEGRACION_LOVABLE.md     <- este archivo
```

## Pasos (en el proyecto de Lovable)

1. **Crea tu proyecto en Lovable** y conéctalo a GitHub (Lovable → GitHub →
   Connect). Eso crea/sincroniza tu repo de la app (ej. `ConciencIA-app`).
2. **Copia el contenido de `public/` de aquí al `public/` de tu repo de Lovable.**
   (En Lovable puedes pedirle: "agrega estos archivos a la carpeta public".)
3. **Pon tu API key de ORS:** copia `ruta_key.example.js` como **`ruta_key.js`**
   (mismo folder `public/`) y pega tu key gratis de <https://openrouteservice.org/dev>.
   Si no lo pones, el mapa pedirá la key con un prompt la primera vez.
4. **Conecta el login a Supabase** (Lovable trae integración nativa: botón Supabase).
5. **Manda al usuario al mapa después del login** (ver snippets abajo).

Listo. La URL `/ruta_segurav2.html` queda servida por Lovable.

---

## Snippets

### Opción A — redirección directa (lo más simple)
Después de un login exitoso con Supabase:
```js
window.location.href = "/ruta_segurav2.html";
```
O un botón en la landing:
```jsx
<a href="/ruta_segurav2.html" className="btn">Entrar al mapa</a>
```

### Opción B — ruta protegida (exige sesión)
Los archivos en `public/` son públicos (cualquiera con la URL los abre). Si quieres
que SÓLO entre con login, embébelo en una ruta protegida con iframe:
```jsx
import { Navigate } from "react-router-dom";
// useSession() = tu hook de sesión de Supabase
function Mapa() {
  const session = useSession();
  if (!session) return <Navigate to="/login" replace />;
  return (
    <iframe
      src="/ruta_segurav2.html"
      title="Ruta segura"
      className="w-full h-[100dvh] border-0"
    />
  );
}
```

**Demo rápida → Opción A. Login obligatorio de verdad → Opción B.**

---

## Asistente de chat (en ruta_segurav2.html)

El botón 💬 abajo-izquierda abre un asistente: el usuario escribe en lenguaje
natural ("llévame a Coyoacán en bici", "de Polanco a CU a pie") y traza la ruta
segura solo. Detección de destino:
- **Con `window.OPENAI_KEY`** (en `ruta_key.js`): usa gpt-4o-mini, entiende frases
  libres. La llamada a OpenAI funciona servida por http(s) (Lovable); en `file://`
  puede bloquear CORS y cae a keywords.
- **Sin key**: modo keyword ("ir a / llévame a / de X a Y") — gratis, sin IA.

## Notas

- Los HTML son **autónomos**: traen el GeoJSON de riesgo embebido. No necesitas
  servir datos aparte.
- El ruteo es en vivo contra ORS; necesita internet (igual que el basemap).
- `ruta_key.js` NO debe ir a un repo público con una key de pago. La free
  rate-limited es aceptable para demo.
- Para regenerar/actualizar los mapas (cambios en datos), corre los scripts del
  repo de datos y vuelve a copiar el `.html` aquí. Repo de datos:
  <https://github.com/RodMed0709/ConciencIA-Micromovilidad>
