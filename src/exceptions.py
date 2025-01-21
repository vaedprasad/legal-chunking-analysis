class FriendlyException(Exception):
    def __init__(
        self,
        detail: str,
        user_friendly_message: str,
        how_to_fix: str,
    ) -> None:
        self.detail = detail
        self.user_friendly_message = user_friendly_message
        self.how_to_fix = how_to_fix

    def __str__(self):
        return f"{self.__class__.__name__}(detail={self.detail!r}, user_friendly_message={self.user_friendly_message!r}, how_to_fix={self.how_to_fix!r})"

    def __repr__(self):
        return f"{self.__class__.__name__}(detail={self.detail!r}, user_friendly_message={self.user_friendly_message!r}, how_to_fix={self.how_to_fix!r})"
