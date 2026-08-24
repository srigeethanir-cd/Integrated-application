typescript
// EmailValidation.ts
interface EmailValidationProps {
  email: string;
  setEmail: (email: string) => void;
}

const EmailValidation: React.FC<EmailValidationProps> = ({ email, setEmail }) => {
  const [emailError, setEmailError] = React.useState<string | null>(null);

  const validateEmail = (email: string) => {
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!emailRegex.test(email)) {
      setEmailError('Invalid email format');
    } else {
      setEmailError(null);
    }
  };

  const handleEmailChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newEmail = event.target.value;
    setEmail(newEmail);
    validateEmail(newEmail);
  };

  return (
    <div>
      <input
        type="email"
        value={email}
        onChange={handleEmailChange}
        placeholder="Enter your email"
      />
      {emailError && <div style={{ color: 'red' }}>{emailError}</div>}
    </div>
  );
};

export default EmailValidation;