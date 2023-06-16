class Chatbox {
    constructor() {
        this.args = {
            openButton: document.querySelector('.chatbox__button'),
            chatBox: document.querySelector('.chatbox__support'),
            sendButton: document.querySelector('.send__button'),
            deleteButton: document.querySelector('.delete__button')
        }

        this.state = false;
        this.messages = [];
    }

    display() {
        const {openButton, chatBox, sendButton, deleteButton} = this.args;

        openButton.addEventListener('click', () => this.toggleState(chatBox))

        sendButton.addEventListener('click', () => this.onSendButton(chatBox))

        deleteButton.addEventListener('click', () => this.deleteChat(chatBox))

        const node = chatBox.querySelector('input');
        node.addEventListener("keyup", ({key}) => {
            if (key === "Enter") {
                this.onSendButton(chatBox)
            }
        })
    }


    toggleState(chatbox) {
        this.state = !this.state;

        // show or hides the box
        if(this.state) {
            chatbox.classList.add('chatbox--active')
        } else {
            chatbox.classList.remove('chatbox--active')
        }
    }

    onSendButton(chatbox) {
        var textField = chatbox.querySelector('input');
        let text1 = textField.value
        if (text1 === "") {
            return;
        }

        let msg1 = { name: "User", message: text1 }
        this.messages.push(msg1);

        fetch('http://127.0.0.1:5000/predict', {
            method: 'POST',
            body: JSON.stringify({ message: text1 }),
            mode: 'cors',
            headers: {
              'Content-Type': 'application/json'
            },
          })
          .then(r => r.json())
          .then(r => {
            let msg2 = { name: "Sam", message: r.answer };
            this.messages.push(msg2);
            this.updateChatText(chatbox)
            textField.value = ''

        }).catch((error) => {
            console.error('Error:', error);
            this.updateChatText(chatbox)
            textField.value = ''
          });
    }

    // updateChatText(chatbox) {
    //     var html = '';
    //     this.messages.slice().reverse().forEach(function(item, index) {
    //         if (item.name === "Sam")
    //         {
    //             html += '<div class="messages__item messages__item--visitor">' + item.message + '</div>'
    //         }
    //         else
    //         {
    //             html += '<div class="messages__item messages__item--operator">' + item.message + '</div>'
    //         }
    //       });

    //     const chatmessage = chatbox.querySelector('.chatbox__messages');
    //     chatmessage.innerHTML = html;
    // }

    updateChatText(chatbox) {
        const chatmessage = chatbox.querySelector('.chatbox__messages');

        // Clear existing messages
        chatmessage.innerHTML = '';

        // Append new messages
        this.messages.forEach((message) => {
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('messages__item');

            if (message.name === 'Sam') {
                messageDiv.classList.add('messages__item--visitor');
            } else {
                messageDiv.classList.add('messages__item--operator');
            }

            messageDiv.textContent = message.message;
            chatmessage.appendChild(messageDiv);
        });
    }
    deleteChat(Chatbox) {

        // Clear the messages array
        this.messages = [];

        // Clear the chatbox content
        const chatmessage = chatbox.querySelector('.chatbox__messages');
        chatmessage.innerHTML = '';

        // Clear the input field
        const textField = chatbox.querySelector('input');
        textField.value = '';
        // not yet updated in real time 
        
    }
}


const chatbox = new Chatbox();
chatbox.display();