# La Gacela NOM-035 Mobile App

Aplicación móvil de demostración personalizada para Manufacturera de Ropa La Gacela bajo la norma NOM-035.

## Instrucciones

1. Instala dependencias:

```powershell
cd mobile_app
npm install
```

2. Inicia Expo:

```powershell
npm run start
```

3. Abre en un emulador o dispositivo con la app Expo Go.

## Configuración

- Ajusta `BACKEND_URL` en `App.js` al host donde corre el backend Flask.
- Para Android con emulador use `http://10.0.2.2:5000`.
- Para iOS use `http://localhost:5000`.
