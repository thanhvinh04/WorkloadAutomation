using System;
using System.Configuration;
using System.Threading.Tasks;
using System.Windows.Forms;
using WorkloadAutomateTool.Services;

namespace WorkloadAutomateTool.Forms
{
    public partial class LoginForm : Form
    {
        private readonly string _customerCode;
        private readonly string _serverUrl;

        public string ServerUrl => _serverUrl;

        public LoginForm(string customerCode, string defaultServerUrl = null)
        {
            InitializeComponent();
            _customerCode = customerCode;
            _serverUrl = defaultServerUrl ?? GetApiBaseUrl();
            
            lblTitle.Text = $"Login - {_customerCode}";
        }

        private string GetApiBaseUrl()
        {
            var env = ConfigurationManager.AppSettings["Environment"] ?? "prod";
            var apiKey = $"ApiBaseUrl_{env.ToLower()}";
            var apiUrl = ConfigurationManager.AppSettings[apiKey];
            
            if (string.IsNullOrEmpty(apiUrl))
                apiUrl = ConfigurationManager.AppSettings["ApiBaseUrl_Prod"];
            
            return (apiUrl ?? "http://172.16.0.5:5000").TrimEnd('/');
        }

        private async void btnLogin_Click(object sender, EventArgs e)
        {
            var server = _serverUrl;
            var username = txtUsername.Text.Trim();
            var password = txtPassword.Text;

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