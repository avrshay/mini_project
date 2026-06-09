from phishguard.types import IncomingMessage, RiskAssessment, RiskTier


class AccessibleAlertManager:
    RED = "\033[1;97;41m"
    YELLOW = "\033[1;30;43m"
    GREEN = "\033[1;30;42m"
    RESET = "\033[0m"

    def __init__(self, high_contrast: bool = True) -> None:
        self.high_contrast = high_contrast

    def notify(self, msg: IncomingMessage, risk: RiskAssessment) -> None:
        header = "התראה מיידית" if risk.tier != RiskTier.SAFE else "עדכון"
        color = self._color_for_tier(risk.tier) if self.high_contrast else ""
        reset = self.RESET if self.high_contrast else ""

        print("\n" + "=" * 72)
        print(f"{color}{header} | {risk.tier.value} | ביטחון בזיהוי: {risk.confidence:.0%}{reset}")
        print(f"הודעה נכנסה מ: {msg.sender} ({msg.channel.value})")
        print(f"טקסט: {msg.text}")
        print(f"הסבר פשוט: {risk.explanation}")

        if risk.tier != RiskTier.SAFE:
            print("מה לעשות עכשיו: אל תלחץ על קישורים. אל תמסור קוד, סיסמה או פרטי אשראי.")
            print("אפשרות בטוחה: התקשר ישירות לחברה הרשמית ממספר שאתה מכיר.")

        print("=" * 72)

    def _color_for_tier(self, tier: RiskTier) -> str:
        if tier == RiskTier.DANGEROUS:
            return self.RED
        if tier == RiskTier.SUSPICIOUS:
            return self.YELLOW
        return self.GREEN

