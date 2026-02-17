(function () {
    function toast(title, message, type, durationMs) {
        const container = document.getElementById('toast-container');
        if (!container) {
            return;
        }

        const toastEl = document.createElement('div');
        toastEl.className = `toast ${type || 'success'}`;

        const titleEl = document.createElement('div');
        titleEl.className = 'toast-title';
        titleEl.textContent = title || '';
        toastEl.appendChild(titleEl);

        if (message) {
            const messageEl = document.createElement('div');
            messageEl.className = 'toast-message';
            messageEl.textContent = message;
            toastEl.appendChild(messageEl);
        }

        container.appendChild(toastEl);
        setTimeout(() => {
            toastEl.remove();
        }, Number.isFinite(durationMs) ? durationMs : 5000);
    }

    function inlineMessage(elementOrId, text, isError) {
        const element = typeof elementOrId === 'string'
            ? document.getElementById(elementOrId)
            : elementOrId;

        if (!element) {
            return;
        }

        element.textContent = text || '';
        element.classList.remove('hidden');
        element.classList.toggle('error', !!isError);
    }

    function confirmAction(options) {
        const title = options?.title || 'Confirm Action';
        const message = options?.message || '';
        const confirmText = options?.confirmText || 'Confirm';
        const cancelText = options?.cancelText || 'Cancel';

        return new Promise((resolve) => {
            const overlay = document.createElement('div');
            overlay.className = 'modal-overlay';

            const card = document.createElement('div');
            card.className = 'modal-card';

            const heading = document.createElement('h3');
            heading.textContent = title;

            const body = document.createElement('p');
            body.className = 'modal-subtext';
            body.textContent = message;

            const actions = document.createElement('div');
            actions.className = 'modal-actions';

            const confirmButton = document.createElement('button');
            confirmButton.type = 'button';
            confirmButton.className = 'mini-btn';
            confirmButton.textContent = confirmText;

            const cancelButton = document.createElement('button');
            cancelButton.type = 'button';
            cancelButton.className = 'mini-btn remove';
            cancelButton.textContent = cancelText;

            function cleanup(result) {
                overlay.remove();
                document.removeEventListener('keydown', handleEsc);
                resolve(result);
            }

            function handleEsc(event) {
                if (event.key === 'Escape') {
                    cleanup(false);
                }
            }

            confirmButton.addEventListener('click', () => cleanup(true));
            cancelButton.addEventListener('click', () => cleanup(false));
            overlay.addEventListener('click', (event) => {
                if (event.target === overlay) {
                    cleanup(false);
                }
            });

            actions.appendChild(confirmButton);
            actions.appendChild(cancelButton);
            card.appendChild(heading);
            card.appendChild(body);
            card.appendChild(actions);
            overlay.appendChild(card);
            document.body.appendChild(overlay);
            document.addEventListener('keydown', handleEsc);
            confirmButton.focus();
        });
    }

    window.UIFeedback = {
        toast,
        inlineMessage,
        confirmAction
    };
})();
