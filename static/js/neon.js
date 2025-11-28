(function () {
    function initNeonScene() {
        const svgLines = document.querySelectorAll('.br-linha');
        if (!svgLines.length) {
            return;
        }

        svgLines.forEach((line, idx) => {
            if (typeof line.getTotalLength !== 'function') {
                return;
            }
            const totalLength = line.getTotalLength();
            const tick = () => {
                const dash = 180 + 40 * Math.sin(Date.now() / 400 + idx);
                const offset = (Date.now() / 6 + idx * 200) % totalLength;
                line.setAttribute('stroke-dasharray', `${dash},${totalLength}`);
                line.setAttribute('stroke-dashoffset', offset);
            };
            setInterval(tick, 30 + idx * 7);
        });

        if (!document.querySelector('.neon-rain')) {
            const rainContainer = document.createElement('div');
            rainContainer.className = 'neon-rain';
            document.body.appendChild(rainContainer);
            for (let i = 0; i < 80; i++) {
                const drop = document.createElement('div');
                drop.className = 'rain-drop';
                drop.style.left = Math.random() * 100 + 'vw';
                drop.style.animationDelay = Math.random() * 3 + 's';
                drop.style.animationDuration = 1.5 + Math.random() * 1.5 + 's';
                rainContainer.appendChild(drop);
            }
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initNeonScene);
    } else {
        initNeonScene();
    }
})();
