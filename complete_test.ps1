# Создаем новый чистый чат без эмодзи
$chatId = "clean_test_$(Get-Date -Format 'HHmmss')"

# Тестовый диалог БЕЗ эмодзи
$dialog = @(
    @{Role = "client"; Text = "Hello! I have a problem with my order"},
    @{Role = "manager"; Text = "Good afternoon! Which order number?"},
    @{Role = "client"; Text = "ORD-789"},
    @{Role = "manager"; Text = "Checking now... Found it! Your order was shipped yesterday."},
    @{Role = "client"; Text = "Thank you! When will it arrive?"},
    @{Role = "manager"; Text = "Delivery takes 5-7 working days. Track it on postal website."}
)

# Отправляем сообщения
foreach ($msg in $dialog) {
    $body = @{
        type = "message"
        message = @{
            id = "msg_$(Get-Random)"
            chatId = $chatId
            text = $msg.Text
            sender = @{
                type = if ($msg.Role -eq "manager") { "operator" } else { "contact" }
                name = $msg.Role
            }
            timestamp = [int](Get-Date -UFormat %s)
        }
    } | ConvertTo-Json
    
    Invoke-RestMethod -Uri "http://localhost:8000/webhook/wazzup" `
      -Method Post `
      -Body $body `
      -ContentType "application/json"
    
    Write-Host "Sent: $($msg.Role) - $($msg.Text)"
    Start-Sleep -Milliseconds 300
}

Write-Host "`nChat created: $chatId"