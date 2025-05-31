/**
 * ユーザー名とその他の入力値の検証関数
 */

/**
 * ユーザー名の検証
 * - 3文字以上50文字以下
 * - アルファベット（a-z, A-Z）と数字（0-9）のみ許可
 * - 特殊文字、スペース、日本語などは不可
 */
export const validateUsername = (username: string): { isValid: boolean; error?: string } => {
  if (!username) {
    return { isValid: false, error: 'ユーザー名は必須です' };
  }

  if (username.length < 3) {
    return { isValid: false, error: 'ユーザー名は3文字以上で入力してください' };
  }

  if (username.length > 50) {
    return { isValid: false, error: 'ユーザー名は50文字以下で入力してください' };
  }

  // アルファベットと数字のみを許可する正規表現
  const usernamePattern = /^[a-zA-Z0-9]+$/;
  if (!usernamePattern.test(username)) {
    return { isValid: false, error: 'ユーザー名はアルファベット（a-z, A-Z）と数字（0-9）のみ使用できます' };
  }

  return { isValid: true };
};

/**
 * ユーザー名の入力を制限する関数
 * 入力時にリアルタイムで無効な文字を除去
 */
export const sanitizeUsername = (input: string): string => {
  // アルファベットと数字以外の文字を除去
  return input.replace(/[^a-zA-Z0-9]/g, '');
};

/**
 * メールアドレスの検証
 */
export const validateEmail = (email: string): { isValid: boolean; error?: string } => {
  if (!email) {
    return { isValid: false, error: 'メールアドレスは必須です' };
  }

  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailPattern.test(email)) {
    return { isValid: false, error: '有効なメールアドレスを入力してください' };
  }

  return { isValid: true };
};

/**
 * パスワードの検証
 */
export const validatePassword = (password: string): { isValid: boolean; error?: string } => {
  if (!password) {
    return { isValid: false, error: 'パスワードは必須です' };
  }

  if (password.length < 8) {
    return { isValid: false, error: 'パスワードは8文字以上で入力してください' };
  }

  return { isValid: true };
};

/**
 * フルネームの検証
 */
export const validateFullName = (fullName: string): { isValid: boolean; error?: string } => {
  if (fullName && fullName.length > 100) {
    return { isValid: false, error: 'フルネームは100文字以下で入力してください' };
  }

  return { isValid: true };
};

/**
 * ユーザー作成フォーム全体の検証
 */
export interface UserFormData {
  email: string;
  username: string;
  full_name?: string;
  password: string;
  confirmPassword?: string;
}

export const validateUserForm = (formData: UserFormData): { isValid: boolean; errors: Record<string, string> } => {
  const errors: Record<string, string> = {};

  // メールアドレス検証
  const emailValidation = validateEmail(formData.email);
  if (!emailValidation.isValid) {
    errors.email = emailValidation.error!;
  }

  // ユーザー名検証
  const usernameValidation = validateUsername(formData.username);
  if (!usernameValidation.isValid) {
    errors.username = usernameValidation.error!;
  }

  // パスワード検証
  const passwordValidation = validatePassword(formData.password);
  if (!passwordValidation.isValid) {
    errors.password = passwordValidation.error!;
  }

  // パスワード確認（存在する場合）
  if (formData.confirmPassword !== undefined) {
    if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = 'パスワードが一致しません';
    }
  }

  // フルネーム検証（存在する場合）
  if (formData.full_name) {
    const fullNameValidation = validateFullName(formData.full_name);
    if (!fullNameValidation.isValid) {
      errors.full_name = fullNameValidation.error!;
    }
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
};
