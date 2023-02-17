class NonceSafe:
    """
    ╔═══════════════════════════════╗
    ║ ╔╗╔╔═╗╔╗╔╔═╗╔═╗  ╔═╗╔═╗╔═╗╔═╗ ║
    ║ ║║║║ ║║║║║  ║╣   ╚═╗╠═╣╠╣ ║╣  ║
    ║ ╝╚╝╚═╝╝╚╝╚═╝╚═╝  ╚═╝╩ ╩╚  ╚═╝ ║
    ╚═══════════════════════════════╝

    context manager for process-safe nonce generation and inter process communication
        nonce generation
        process safe read
        process safe write
        process safe atomic read/write
    wtfpl litepresence.com 2022
    """

    @staticmethod
    def __enter__(*_) -> None:
        """
        file lock: try until success to change name of nonce.vacant to nonce.occupied
        """
        if not os.path.exists(f"{PATH}nonce_safe/nonce.vacant") and not os.path.exists(
            f"{PATH}nonce_safe/nonce.occupied"
        ):
            NonceSafe.restart()
        while True:
            # fails when nonce.occupied
            try:
                os.rename("nonce_safe/nonce.vacant", "nonce_safe/nonce.occupied")
                break
            except Exception:
                time.sleep(0.01)

    @staticmethod
    def __exit__(*_) -> None:
        """
        file unlock : change name of nonce.occupied back to nonce.vacant
        """
        os.rename("nonce_safe/nonce.occupied", "nonce_safe/nonce.vacant")

    @staticmethod
    def restart() -> None:
        """
        new locker: on startup, delete directory and start fresh
        """
        os.system(
            f"rm -r {PATH}nonce_safe; "
            + f"mkdir {PATH}nonce_safe; "
            + f"touch {PATH}nonce_safe/nonce.vacant"
        )
        thread = Thread(target=NonceSafe.free)
        thread.start()

    @staticmethod
    def free() -> None:
        """
        the nonce locker should never be occupied for more than a few milliseconds
        plausible the locker could get stuck, e.g. a process terminates while occupied
        """
        while True:
            # check every three seconds if the nonce is vacant
            if os.path.exists(f"{PATH}nonce_safe/nonce.vacant"):
                time.sleep(3)
            else:
                # check repeatedly for 3 seconds for vacancy
                start = time.time()
                while True:
                    elapsed = time.time() - start
                    if os.path.exists(f"{PATH}nonce_safe/nonce.vacant"):
                        break
                    # liberate the nonce locker
                    if elapsed > 3:
                        os.rename(
                            "nonce_safe/nonce.occupied", "nonce_safe/nonce.vacant"
                        )


def get_nonce(precision: int = 1e9) -> int:
    """
    :param precision: int(10^n)
    :return nonce:
    """
    with NonceSafe():
        now = int(time.time() * precision)
        while True:
            nonce = int(time.time() * precision)
            if nonce > now:
                return nonce
            time.sleep(1 / (10 * precision))

