$body = @{ username = 'user'; password = 'password' } | ConvertTo-Json -Compress
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8000/api/login' -Body $body -ContentType 'application/json' | ConvertTo-Json
