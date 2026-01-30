# accounts/email_validator.py

import re
from typing import Tuple, Optional

class EmailValidator:
    """
    Utility class for validating email addresses.
    Detects disposable emails, validates format, and suggests corrections.
    """
    
    # List of known disposable/temporary email domains
    # Source: https://github.com/disposable-email-domains/disposable-email-domains
    DISPOSABLE_DOMAINS = {
        '10minutemail.com', '10minutemail.net', '10minutemail.org',
        'guerrillamail.com', 'guerrillamail.net', 'guerrillamail.org',
        'mailinator.com', 'maildrop.cc', 'temp-mail.org', 'tempmail.com',
        'throwaway.email', 'yopmail.com', 'getnada.com', 'trashmail.com',
        'fakeinbox.com', 'sharklasers.com', 'grr.la', 'guerrillamailblock.com',
        'pokemail.net', 'spam4.me', 'tempinbox.com', 'throwawaymail.com',
        'mintemail.com', 'mytemp.email', 'temp-mail.io', 'emailondeck.com',
        'mohmal.com', 'mailnesia.com', 'mailcatch.com', 'dispostable.com',
        'burnermail.io', 'getairmail.com', 'harakirimail.com', 'jetable.org',
        'mailexpire.com', 'mailforspam.com', 'mailfreeonline.com', 'mailin8r.com',
        'mailmoat.com', 'mailnull.com', 'mailsac.com', 'mailtemp.info',
        'meltmail.com', 'mintemail.com', 'mytrashmail.com', 'no-spam.ws',
        'nospam.ze.tc', 'nospamfor.us', 'nowmymail.com', 'objectmail.com',
        'obobbo.com', 'oneoffemail.com', 'onewaymail.com', 'pookmail.com',
        'proxymail.eu', 'put2.net', 'quickinbox.com', 'rcpt.at',
        'recode.me', 'recursor.net', 'rppkn.com', 's0ny.net',
        'safe-mail.net', 'safetymail.info', 'safetypost.de', 'sandelf.de',
        'saynotospams.com', 'selfdestructingmail.com', 'sendspamhere.com',
        'shiftmail.com', 'skeefmail.com', 'slaskpost.se', 'slopsbox.com',
        'smellfear.com', 'snakemail.com', 'sneakemail.com', 'sofimail.com',
        'solvemail.info', 'spam.la', 'spamavert.com', 'spambob.com',
        'spambob.net', 'spambog.com', 'spambog.de', 'spambog.ru',
        'spambox.us', 'spamcannon.com', 'spamcannon.net', 'spamcon.org',
        'spamcorptastic.com', 'spamcowboy.com', 'spamcowboy.net', 'spamcowboy.org',
        'spamday.com', 'spamex.com', 'spamfree24.com', 'spamfree24.de',
        'spamfree24.eu', 'spamfree24.info', 'spamfree24.net', 'spamfree24.org',
        'spamgourmet.com', 'spamgourmet.net', 'spamgourmet.org', 'spamherelots.com',
        'spamhereplease.com', 'spamhole.com', 'spamify.com', 'spaml.com',
        'spaml.de', 'spammotel.com', 'spamobox.com', 'spamspot.com',
        'spamthis.co.uk', 'spamthisplease.com', 'spamtrail.com', 'speed.1s.fr',
        'supergreatmail.com', 'supermailer.jp', 'suremail.info', 'teewars.org',
        'teleworm.com', 'teleworm.us', 'temp-mail.com', 'temp-mail.de',
        'temp-mail.ru', 'tempalias.com', 'tempe-mail.com', 'tempemail.biz',
        'tempemail.co.za', 'tempemail.com', 'tempemail.net', 'tempinbox.co.uk',
        'tempmail.eu', 'tempmail.it', 'tempmail2.com', 'tempmaildemo.com',
        'tempmailer.com', 'tempmailer.de', 'tempomail.fr', 'temporarily.de',
        'temporarioemail.com.br', 'temporaryemail.net', 'temporaryemail.us',
        'temporaryforwarding.com', 'temporaryinbox.com', 'temporarymailaddress.com',
        'thanksnospam.info', 'thankyou2010.com', 'thc.st', 'thelimestones.com',
        'thisisnotmyrealemail.com', 'thismail.net', 'throwawayemailaddress.com',
        'tilien.com', 'tittbit.in', 'tizi.com', 'tmailinator.com',
        'toomail.biz', 'topranklist.de', 'tradermail.info', 'trash-amil.com',
        'trash-mail.at', 'trash-mail.com', 'trash-mail.de', 'trash2009.com',
        'trashemail.de', 'trashmail.at', 'trashmail.com', 'trashmail.de',
        'trashmail.me', 'trashmail.net', 'trashmail.org', 'trashmail.ws',
        'trashmailer.com', 'trashymail.com', 'trashymail.net', 'trialmail.de',
        'trillianpro.com', 'turual.com', 'twinmail.de', 'tyldd.com',
        'uggsrock.com', 'umail.net', 'uroid.com', 'us.af',
        'venompen.com', 'veryrealemail.com', 'viditag.com', 'viewcastmedia.com',
        'viewcastmedia.net', 'viewcastmedia.org', 'webm4il.info', 'wegwerfadresse.de',
        'wegwerfemail.de', 'wegwerfmail.de', 'wegwerfmail.net', 'wegwerfmail.org',
        'wetrainbayarea.com', 'wetrainbayarea.org', 'wh4f.org', 'whyspam.me',
        'willselfdestruct.com', 'winemaven.info', 'wronghead.com', 'wuzup.net',
        'wuzupmail.net', 'www.e4ward.com', 'www.gishpuppy.com', 'www.mailinator.com',
        'wwwnew.eu', 'x.ip6.li', 'xagloo.com', 'xemaps.com',
        'xents.com', 'xmaily.com', 'xoxy.net', 'yapped.net',
        'yopmail.fr', 'yopmail.net', 'yourdomain.com', 'yuurok.com',
        'z1p.biz', 'za.com', 'zehnminuten.de', 'zehnminutenmail.de',
        'zippymail.info', 'zoemail.net', 'zomg.info',
    }
    
    # Common email domain typos and their corrections
    DOMAIN_CORRECTIONS = {
        'gmai.com': 'gmail.com',
        'gmial.com': 'gmail.com',
        'gmil.com': 'gmail.com',
        'yahooo.com': 'yahoo.com',
        'yaho.com': 'yahoo.com',
        'hotmial.com': 'hotmail.com',
        'hotmai.com': 'hotmail.com',
        'outlok.com': 'outlook.com',
        'outloo.com': 'outlook.com',
    }
    
    # Email regex pattern (RFC 5322 simplified)
    EMAIL_REGEX = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    @staticmethod
    def is_valid_format(email: str) -> bool:
        """
        Check if email has valid format.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if format is valid, False otherwise
        """
        if not email:
            return False
        return bool(EmailValidator.EMAIL_REGEX.match(email))
    
    @staticmethod
    def is_disposable_email(email: str) -> bool:
        """
        Check if email is from a disposable/temporary email service.
        
        Args:
            email: Email address to check
            
        Returns:
            True if disposable, False otherwise
        """
        if not email or '@' not in email:
            return False
        
        domain = email.split('@')[1].lower()
        return domain in EmailValidator.DISPOSABLE_DOMAINS
    
    @staticmethod
    def suggest_correction(email: str) -> Optional[str]:
        """
        Suggest correction for common email typos.
        
        Args:
            email: Email address to check
            
        Returns:
            Suggested correction or None if no correction needed
        """
        if not email or '@' not in email:
            return None
        
        local_part, domain = email.rsplit('@', 1)
        domain_lower = domain.lower()
        
        if domain_lower in EmailValidator.DOMAIN_CORRECTIONS:
            return f"{local_part}@{EmailValidator.DOMAIN_CORRECTIONS[domain_lower]}"
        
        return None
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Comprehensive email validation.
        
        Args:
            email: Email address to validate
            
        Returns:
            Tuple of (is_valid, error_message, suggestion)
            - is_valid: True if email passes all checks
            - error_message: Error message if validation fails, None otherwise
            - suggestion: Suggested correction if typo detected, None otherwise
        """
        if not email:
            return False, "Email address is required.", None
        
        email = email.strip().lower()
        
        # Check format
        if not EmailValidator.is_valid_format(email):
            return False, "Please enter a valid email address.", None
        
        # Check for typos
        suggestion = EmailValidator.suggest_correction(email)
        if suggestion:
            return False, f"Did you mean {suggestion}?", suggestion
        
        # Check for disposable emails
        if EmailValidator.is_disposable_email(email):
            return False, "Disposable email addresses are not allowed. Please use a permanent email address.", None
        
        return True, None, None
    
    @staticmethod
    def validate_and_normalize(email: str) -> Tuple[bool, str, Optional[str]]:
        """
        Validate email and return normalized version.
        
        Args:
            email: Email address to validate
            
        Returns:
            Tuple of (is_valid, normalized_email, error_message)
        """
        is_valid, error_message, suggestion = EmailValidator.validate_email(email)
        
        if is_valid:
            return True, email.strip().lower(), None
        else:
            return False, email, error_message
