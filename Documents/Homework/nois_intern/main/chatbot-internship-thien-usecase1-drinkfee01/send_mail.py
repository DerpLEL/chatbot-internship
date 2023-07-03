import smtplib

server = smtplib.SMTP('smtp.gmail.com',587)

server.starttls()

server.login('tranquangthien31@gmail.com', 'quangteldaktnthien2')

server.sendmail('tranquangthien31@gmail.com', 'tranquangthien11114@gmail.com', 'Hello')

print('Sent mail')