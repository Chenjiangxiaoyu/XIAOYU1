import cors from 'cors'
import express from 'express'

const app = express()
app.use(cors())
app.use(express.json())
app.get('/api/health', (_request, response) => response.json({ status: 'ok' }))

const port = Number(process.env.PORT ?? 3000)
app.listen(port, () => console.log(`API listening on http://localhost:${port}`))
