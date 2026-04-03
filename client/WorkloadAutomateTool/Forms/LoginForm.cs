using System;
using System.Threading.Tasks;
using System.Windows.Forms;
using WorkloadAutomateTool.Services;

namespace WorkloadAutomateTool.Forms
{
    public partial class LoginForm : Form
    {
        private readonly string _customerCode;
        private readonly string _defaultServerUrl;

        public string ServerUrl => txtServerUrl.Text.Trim();

        public LoginForm(string customerCode, string defaultServerUrl = null)
        {
            InitializeComponent();
            _customerCode = customerCode;
            _defaultServerUrl = defaultServerUrl ?? GetDefaultServerUrl(customerCode);
            
            txtServerUrl.Text = _defaultServerUrl;
            lblTitle.Text = $"Login - {_customerCode}";
        }

        private string GetDefaultServerUrl(string customer)
        {
            switch (customer)
            {
                case "HADDAD":
                    return "http://125.234.111.210:8000";
                case "LTD":
                    return "http://125.234.111.210:8000";
                case "GARAN":
                    return "http://125.234.111.210:8000";
                default:
                    return "http://127.0.0.1:8000";
            }
        }

        private async void btnLogin_Click(object sender, EventArgs e)
        {
            var server = txtServerUrl.Text.Trim();
            var username = txtUsername.Text.Trim();
            var password = txtPassword.Text;

            if (string.IsNullOrEmpty(server))
            {
                MessageBox.Show("Please enter server URL.", "Validation", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            if (string.IsNullOrEmpty(username))
            {
                MessageBox.Show("Please enter username.", "Validation", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            if (string.IsNullOrEmpty(password))
            {
                MessageBox.Show("Please enter password.", "Validation", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            btnLogin.Enabled = false;
            txtPassword.Enabled = false;
            lblStatus.Text = "Logging in...";
            lblStatus.Visible = true;

            try
            {
                AuthService.Instance.SetServerUrl(server);
                var (success, message) = await AuthService.Instance.Login(_customerCode, username, password);

                if (success)
                {
                    this.DialogResult = DialogResult.OK;
                    this.Close();
                }
                else
                {
                    lblStatus.Text = message;
                    MessageBox.Show(message, "Login Failed", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }
            catch (Exception ex)
            {
                lblStatus.Text = "Error: " + ex.Message;
                MessageBox.Show(ex.Message, "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
            finally
            {
                btnLogin.Enabled = true;
                txtPassword.Enabled = true;
                if (this.DialogResult != DialogResult.OK)
                {
                    lblStatus.Text = "Login failed";
                }
            }
        }

        private void btnCancel_Click(object sender, EventArgs e)
        {
            this.DialogResult = DialogResult.Cancel;
            this.Close();
        }

        private void txtPassword_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.KeyCode == Keys.Enter)
            {
                btnLogin_Click(sender, e);
            }
        }
    }
}
