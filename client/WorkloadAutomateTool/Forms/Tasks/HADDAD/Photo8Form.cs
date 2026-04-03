using OpenQA.Selenium;
using OpenQA.Selenium.Chrome;
using OpenQA.Selenium.Support.UI;
using System;
using System.Windows.Forms;
using SeleniumExtras.WaitHelpers;
using System.Collections.Generic;
using System.Linq;
using System.Data.SqlClient;
using System.Data;
using System.Configuration;
using System.IO;
using System.Text.RegularExpressions;
using System.Threading;

namespace WorkloadAutomateTool.Forms.Tasks.HADDAD
{
    public partial class Photo8Form : Form
    {
        private IWebDriver driver;
        private int checkProcess;
        private DataTable dt = new DataTable();

        public Photo8Form()
        {
            InitializeComponent();
            checkProcess = 0;
            txtImagePath.Text = Properties.Settings.Default.Image;
            txtType.Text = Properties.Settings.Default.Type;
            txtContractor.Text = Properties.Settings.Default.Contractor;
            txtSeason.Text = Properties.Settings.Default.Season;
        }

        private string GetChromeProfilePath()
        {
            if (!string.IsNullOrEmpty(Properties.Settings.Default.ChromeProfilePath)
                && Directory.Exists(Properties.Settings.Default.ChromeProfilePath))
            {
                return Properties.Settings.Default.ChromeProfilePath;
            }

            using (var dialog = new FolderBrowserDialog())
            {
                dialog.Description = "Chon thu muc luu Chrome Selenium Profile";
                dialog.ShowNewFolderButton = true;

                if (dialog.ShowDialog() != DialogResult.OK)
                    throw new Exception("Chua chon thu muc luu Chrome profile.");

                string profilePath = Path.Combine(dialog.SelectedPath, "ChromeAuthProfile");
                Directory.CreateDirectory(profilePath);

                Properties.Settings.Default.ChromeProfilePath = profilePath;
                Properties.Settings.Default.Save();

                return profilePath;
            }
        }

        private void BtnSelectFolder_Click(object sender, EventArgs e)
        {
            using (FolderBrowserDialog fbd = new FolderBrowserDialog())
            {
                fbd.Description = "Chon folder chua hinh anh";
                fbd.ShowNewFolderButton = false;

                if (fbd.ShowDialog() == DialogResult.OK)
                {
                    txtImagePath.Text = fbd.SelectedPath;
                }
            }
        }

        private void BtnLogin_Click(object sender, EventArgs e)
        {
            try
            {
                string profilePath = GetChromeProfilePath();

                if (!Directory.Exists(profilePath))
                    Directory.CreateDirectory(profilePath);

                ChromeOptions options = new ChromeOptions();
                options.AddArgument("--start-maximized");
                options.AddArgument($"--user-data-dir={profilePath}");

                driver = new ChromeDriver(options);
                driver.Navigate().GoToUrl("https://workloadautomation.haddad.com/");
                lblStatus.Text = "Status: Login Sucess!";
                checkProcess = 1;
                checkProcess = 2;
            }
            catch (Exception ex)
            {
                if (driver != null)
                {
                    driver.Quit();
                    driver = null;
                    lblStatus.Text = "Status: Login Fail!";
                }
                checkProcess = 0;
                MessageBox.Show(ex.Message);
            }
        }

        private void BtnLoadTasks_Click(object sender, EventArgs e)
        {
            try
            {
                if (driver == null)
                {
                    MessageBox.Show("Ban chua dang nhap!");
                    return;
                }

                string rawInputLb = rtbLabel.Text;
                string rawInputPO = rtbPO.Text;
                string contractNo = txtContractNo.Text;
                string contractor = txtContractor.Text;
                string season = txtSeason.Text;

                var labelList = rawInputLb
                    .Split(new[] { ',', '\n', '\r' }, StringSplitOptions.RemoveEmptyEntries)
                    .Select(x => x.Trim())
                    .Where(x => !string.IsNullOrWhiteSpace(x))
                    .Distinct()
                    .ToList();
                var poList = rawInputPO
                    .Split(new[] { ',', '\n', '\r' }, StringSplitOptions.RemoveEmptyEntries)
                    .Select(x => x.Trim())
                    .Where(x => !string.IsNullOrWhiteSpace(x))
                    .Distinct()
                    .ToList();

                if ((labelList.Count == 0 || string.IsNullOrWhiteSpace(contractNo)
                    || string.IsNullOrWhiteSpace(contractor)
                    || string.IsNullOrWhiteSpace(season)
                    ) && poList.Count == 0)
                {
                    MessageBox.Show("Vui long nhap du Contractor-ContractNo-Season-Label hoac nhap theo PO");
                    return;
                }

                lblStatus.Text = "Status: Processing...";

                if (poList.Count == 0)
                {
                    var parameters = labelList.Select((label, index) => $"@p{index}").ToList();
                    string sql = $@"
                    SELECT PurchaseOrderNumber,
                        CASE WHEN Season = 'M' THEN 'Summer ' WHEN Season = 'F' THEN 'Fall '
                             WHEN Season = 'S' THEN 'Spring ' WHEN Season = 'H' THEN 'Holiday ' END + cast(Year as nvarchar(4)) Season,
                        ContractNo, CustomerStyle, FORMAT(ShipDate, 'MMM dd, yyyy', 'en-US') AS ShipDateText,
                        ColorCode, LabelCode, Account, Contractor, Length, Width, Height, NetWeight, GrossWeight, QuantityPerCarton
                    FROM ItemStyle i
                    LEFT JOIN (SELECT LSStyle, MAX(TRY_CAST(Length as float)) Length, MAX(TRY_CAST(Width as float)) Width,
                        MAX(TRY_CAST(Height as float)) Height, MAX(TRY_CAST(NetWeight as float)) NetWeight,
                        MAX(TRY_CAST(GrossWeight as float)) GrossWeight, MAX(TRY_CAST(QuantityPerCarton as float)) QuantityPerCarton
                        FROM PackingLine WHERE IsDeleted = 0 GROUP BY LSStyle) p
                    ON p.LSStyle = i.LSStyle AND i.IsDeleted = 0 AND ISNULL(ItemStyleStatusCode,1) <> 3
                    WHERE LabelCode IN ({string.Join(",", parameters)}) AND ContractNo = '{contractNo}' AND Contractor = '{contractor}'
                    AND (Season + right(cast(Year as nvarchar(4)),2) = '{season}' OR Season + cast(Year as nvarchar(4)) = '{season}')";

                    string connStr = ConfigurationManager.ConnectionStrings["MyDbConnectionPro"].ConnectionString;
                    using (SqlConnection conn = new SqlConnection(connStr))
                    using (SqlCommand cmd = new SqlCommand(sql, conn))
                    {
                        for (int i = 0; i < labelList.Count; i++) cmd.Parameters.AddWithValue($"@p{i}", labelList[i]);
                        conn.Open();
                        using (SqlDataAdapter da = new SqlDataAdapter(cmd)) da.Fill(dt);
                    }
                }
                else
                {
                    var parameters = poList.Select((po, index) => $"@p{index}").ToList();
                    string sql = $@"
                    SELECT PurchaseOrderNumber,
                        CASE WHEN Season = 'M' THEN 'Summer ' WHEN Season = 'F' THEN 'Fall '
                             WHEN Season = 'S' THEN 'Spring ' WHEN Season = 'H' THEN 'Holiday ' END + cast(Year as nvarchar(4)) Season,
                        ContractNo, CustomerStyle, FORMAT(ShipDate, 'MMM dd, yyyy', 'en-US') AS ShipDateText,
                        ColorCode, LabelCode, Account, Contractor, Length, Width, Height, NetWeight, GrossWeight, QuantityPerCarton
                    FROM ItemStyle i
                    LEFT JOIN (SELECT LSStyle, MAX(TRY_CAST(Length as float)) Length, MAX(TRY_CAST(Width as float)) Width,
                        MAX(TRY_CAST(Height as float)) Height, MAX(TRY_CAST(NetWeight as float)) NetWeight,
                        MAX(TRY_CAST(GrossWeight as float)) GrossWeight, MAX(TRY_CAST(QuantityPerCarton as float)) QuantityPerCarton
                        FROM PackingLine WHERE IsDeleted = 0 GROUP BY LSStyle) p
                    ON p.LSStyle = i.LSStyle AND i.IsDeleted = 0 AND ISNULL(ItemStyleStatusCode,1) <> 3
                    WHERE PurchaseOrderNumber IN ({string.Join(",", parameters)})";

                    string connStr = ConfigurationManager.ConnectionStrings["MyDbConnectionPro"].ConnectionString;
                    using (SqlConnection conn = new SqlConnection(connStr))
                    using (SqlCommand cmd = new SqlCommand(sql, conn))
                    {
                        for (int i = 0; i < poList.Count; i++) cmd.Parameters.AddWithValue($"@p{i}", poList[i]);
                        conn.Open();
                        using (SqlDataAdapter da = new SqlDataAdapter(cmd)) da.Fill(dt);
                    }
                }

                dataGridView1.DataSource = dt;
                if (dt.Rows.Count == 0)
                {
                    MessageBox.Show("Khong co du lieu!");
                    return;
                }

                var type = txtType.Text.ToUpper();
                if (type != "HBNYO" && type != "HBE")
                {
                    MessageBox.Show("Type khong hop le!");
                    return;
                }

                driver.Navigate().GoToUrl("https://workloadautomation.haddad.com/Create");
                WebDriverWait wait = new WebDriverWait(driver, TimeSpan.FromSeconds(100));
                var typebutton = wait.Until(d => d.FindElement(By.XPath("//button[contains(., '" + type + "')]")));
                typebutton.Click();

                FillCreateRequest(dt);

                checkProcess = 2;
                lblStatus.Text = "Status: Waiting...";
                MessageBox.Show("Tasks Done!");
            }
            catch (Exception ex)
            {
                checkProcess = 0;
                MessageBox.Show(ex.Message);
                if (driver != null) { driver.Quit(); driver = null; }
            }
        }

        private void FillCreateRequest(DataTable dt)
        {
            WebDriverWait wait = new WebDriverWait(driver, TimeSpan.FromSeconds(100));
            lblStatus.Text = "Status: Fill Draft...";

            var season = dt.AsEnumerable().Select(r => r["Season"].ToString()).FirstOrDefault();
            var dropdown = wait.Until(d => d.FindElement(By.XPath("//div[contains(@class,'rw-dropdown-list-input')]")));
            dropdown.Click();
            var input = wait.Until(d => d.FindElement(By.XPath("//div[contains(@class,'rw-input')]//input[not(@tabindex='-1')]")));
            wait.Until(ExpectedConditions.ElementToBeClickable(input));
            input.SendKeys(season);
            input.SendKeys(OpenQA.Selenium.Keys.Enter);

            lblStatus.Text = "Status: Fill Factory...";
            var factory = dt.AsEnumerable().Select(r => r["Contractor"].ToString()).Distinct().First();
            input = driver.FindElement(By.CssSelector(".searchable-dropdown input"));
            input.Clear();
            input.SendKeys(factory);
            input.SendKeys(OpenQA.Selenium.Keys.Enter);

            lblStatus.Text = "Status: Fill Reference Number...";
            var refInput = driver.FindElement(By.XPath("//div[@class='field-label' and text()='Reference Number']/following::input[1]"));
            var refText = dt.AsEnumerable().Select(r => r["ContractNo"].ToString()).FirstOrDefault();
            refInput.Click();
            refInput.Clear();
            refInput.SendKeys(refText);
            refInput.SendKeys(OpenQA.Selenium.Keys.Enter);

            lblStatus.Text = "Status: Fill Colors...";
            var colors = dt.AsEnumerable().Select(r => r["ColorCode"].ToString()).Distinct().ToList();
            foreach (var color in colors)
            {
                var colorInput = wait.Until(d => d.FindElement(By.XPath("//div[@class='field-label' and normalize-space()='Colors']/following-sibling::div//div[contains(@class,'searchable-dropdown')]//input")));
                colorInput.Click();
                colorInput.Clear();
                colorInput.SendKeys(color);
                colorInput.SendKeys(OpenQA.Selenium.Keys.Enter);
                wait.Until(d => d.FindElements(By.XPath("//div[contains(@class,'selected-items')]//div[contains(@class,'selected-item')]//div[@class='value']")).Any(s => s.Text.Trim().Equals(color, StringComparison.OrdinalIgnoreCase)));
            }

            lblStatus.Text = "Status: Fill Styles...";
            var styles = dt.AsEnumerable().Select(r => r["CustomerStyle"].ToString()).Distinct().ToList();
            var styleInput = wait.Until(d => d.FindElement(By.XPath("//div[@class='field-label' and normalize-space()='Styles']/following-sibling::div//div[contains(@class,'searchable-dropdown')]//input")));
            foreach (var style in styles)
            {
                styleInput = wait.Until(d => d.FindElement(By.XPath("//div[@class='field-label' and normalize-space()='Styles']/following-sibling::div//div[contains(@class,'searchable-dropdown')]//input")));
                styleInput.Click();
                styleInput.SendKeys(style);
                styleInput.SendKeys(OpenQA.Selenium.Keys.Enter);
                wait.Until(d => { styleInput.SendKeys(OpenQA.Selenium.Keys.Enter); return d.FindElements(By.XPath("//div[contains(@class,'selected-items')]//div[contains(@class,'selected-item')]//div[@class='value']")).Any(s => s.Text.Trim().Equals(style, StringComparison.OrdinalIgnoreCase)); });
            }

            lblStatus.Text = "Status: Fill Labels...";
            var labels = dt.AsEnumerable().Select(r => r["LabelCode"].ToString()).Distinct().ToList();
            foreach (var label in labels)
            {
                var labelInput = wait.Until(d => d.FindElement(By.XPath("//div[@class='field-label' and normalize-space()='Labels']/following-sibling::div//div[contains(@class,'searchable-dropdown')]//input")));
                labelInput.Click();
                labelInput.SendKeys(label);
                labelInput.SendKeys(OpenQA.Selenium.Keys.Enter);
                wait.Until(d => d.FindElements(By.XPath("//div[contains(@class,'selected-items')]//div[contains(@class,'selected-item')]//div[@class='value']")).Any(s => s.Text.Trim().Equals(label, StringComparison.OrdinalIgnoreCase)));
            }

            lblStatus.Text = "Status: Fill ShipDate...";
            var shipdates = dt.AsEnumerable().Select(r => r["ShipDateText"].ToString()).Distinct().ToList();
            int idx = 1;
            foreach (var ship in shipdates)
            {
                var shipDate1 = wait.Until(d => d.FindElement(By.XPath("//div[@class='field-label' and normalize-space()='Ship Dates']/following::input[" + idx + "]")));
                shipDate1.Click();
                shipDate1.SendKeys(ship);
                shipDate1.SendKeys(OpenQA.Selenium.Keys.Enter);
                styleInput.Click();
                idx++;
            }

            lblStatus.Text = "Status: Fill Customer...";
            var customerInput = wait.Until(d => d.FindElement(By.XPath("//div[@class='field-label' and normalize-space()='Customer']/following::div[contains(@class,'searchable-dropdown')]//input")));
            customerInput.Click();
            customerInput.Clear();
            string customerName = dt.AsEnumerable().Select(r => r["Account"].ToString()).FirstOrDefault();
            customerInput.SendKeys(customerName);
            customerInput.SendKeys(OpenQA.Selenium.Keys.Enter);
            var firstItem = wait.Until(ExpectedConditions.ElementToBeClickable(By.XPath("(//div[contains(@class,'list')]//div[contains(@class,'item')])[1]")));
            firstItem.Click();

            lblStatus.Text = "Status: Select POs...";
            var poList = dt.AsEnumerable().Select(r => r["PurchaseOrderNumber"].ToString()).Distinct().ToList();
            wait.Until(d => d.FindElements(By.CssSelector(".checkbox-list input[type='checkbox']")).Count > 0);
            foreach (var po in poList)
            {
                try
                {
                    var checkbox = driver.FindElement(By.Id(po));
                    if (!checkbox.Selected) ((IJavaScriptExecutor)driver).ExecuteScript("arguments[0].click();", checkbox);
                }
                catch { }
            }
        }

        private void BtnSave_Click(object sender, EventArgs e)
        {
            if (checkProcess != 2)
            {
                MessageBox.Show("Need Login and Load Draft before!");
                return;
            }

            try
            {
                WebDriverWait wait = new WebDriverWait(driver, TimeSpan.FromSeconds(100));
                var saveDraftBtn = wait.Until(d => d.FindElement(By.XPath("//div[contains(@class,'default-header')]//button[normalize-space()='Save Draft']")));
                saveDraftBtn.Click();

                bool isError = false;
                wait.Until(d =>
                {
                    if (d.Url.Contains("/Details/GeneralInfo")) return true;
                    var error = d.FindElements(By.XPath("//div[contains(@class,'message-modal') and contains(.,' was not saved')]"));
                    if (error.Any()) { isError = true; return true; }
                    return false;
                });

                if (isError)
                {
                    MessageBox.Show("Save Draft failed!");
                    return;
                }

                string currentUrl = driver.Url;
                while (!currentUrl.Contains("Details")) currentUrl = driver.Url;
                string baseUrl = Regex.Match(currentUrl, @"^.+?/Details").Value;

                var tags = new List<string> { "Components", "Packing", "Garment", "ClosedCarton" };
                foreach (var tag in tags)
                {
                    driver.Navigate().GoToUrl(baseUrl + $"/{tag}");
                    wait = new WebDriverWait(driver, TimeSpan.FromSeconds(100));
                    var groupNames = wait.Until(d => { var els = d.FindElements(By.XPath("//div[@class='group-name']")); return els.Count > 0 ? els : null; });
                    var groupNameTexts = groupNames.Select(g => g.Text.Trim()).Where(t => !string.IsNullOrEmpty(t)).ToList();

                    foreach (var groupName in groupNameTexts)
                    {
                        var files = Directory.GetFiles(txtImagePath.Text).Where(f => Path.GetFileName(f).StartsWith(groupName.Trim(), StringComparison.OrdinalIgnoreCase)).ToArray();
                        if (files.Length == 0) continue;

                        var attachments = wait.Until(d => d.FindElement(By.XPath($"//div[@class='group'][.//div[@class='group-name' and translate(normalize-space(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = '{groupName.ToLower()}']]//div[@class='attachments']")));
                        var tiles = attachments.FindElement(By.XPath("./div[@class='tiles']"));
                        ((IJavaScriptExecutor)driver).ExecuteScript("arguments[0].scrollIntoView({block:'center'});", tiles);
                        ((IJavaScriptExecutor)driver).ExecuteScript("arguments[0].click();", tiles);

                        var modal = wait.Until(d => d.FindElements(By.XPath("//div[contains(@class,'upload-file-modal')]")).FirstOrDefault(x => x.Displayed));
                        var fileInput = wait.Until(d => modal.FindElement(By.XPath(".//input[@type='file']")));
                        ((IJavaScriptExecutor)driver).ExecuteScript("arguments[0].style.display='block'; arguments[0].value='';", fileInput);
                        fileInput.SendKeys(string.Join("\n", files));

                        var saveBtn = wait.Until(ExpectedConditions.ElementToBeClickable(By.XPath("//div[contains(@class,'upload-file-modal')]//button[normalize-space()='Save']")));
                        ((IJavaScriptExecutor)driver).ExecuteScript("arguments[0].click();", saveBtn);
                        wait.Until(d => d.FindElements(By.XPath("//div[contains(@class,'upload-file-modal')]")).Count == 0 || d.FindElements(By.XPath("//div[contains(@class,'upload-file-modal')]")).All(x => !x.Displayed));
                        wait.Until(d => ((IJavaScriptExecutor)d).ExecuteScript("return document.readyState").ToString() == "complete");
                    }

                    saveDraftBtn = wait.Until(ExpectedConditions.ElementToBeClickable(By.XPath("//button[normalize-space()='Save Draft']")));
                    ((IJavaScriptExecutor)driver).ExecuteScript("arguments[0].scrollIntoView({block:'center'});", saveDraftBtn);
                    Thread.Sleep(2000);

                    if (tag == "ClosedCarton")
                    {
                        var cartons = new List<CartonData>();
                        foreach (DataRow row in dt.Rows)
                        {
                            if (row["PurchaseOrderNumber"] == DBNull.Value) continue;
                            cartons.Add(new CartonData
                            {
                                PO = row["PurchaseOrderNumber"].ToString().Trim(),
                                Length = row["Length"]?.ToString(),
                                Width = row["Width"]?.ToString(),
                                Height = row["Height"]?.ToString(),
                                NetWeight = row["NetWeight"]?.ToString(),
                                GrossWeight = row["GrossWeight"]?.ToString()
                            });
                        }

                        foreach (var data in cartons)
                        {
                            var carton = TryWaitCarton(driver, data.PO);
                            if (carton == null) continue;

                            void Fill(string label, string value)
                            {
                                if (string.IsNullOrWhiteSpace(value)) return;
                                try
                                {
                                    var input = carton.FindElement(By.XPath($".//div[@class='field'][.//div[text()='{label}']]//input"));
                                    ((IJavaScriptExecutor)driver).ExecuteScript("arguments[0].value = '';", input);
                                    input.SendKeys(value);
                                }
                                catch { }
                            }

                            Fill("Length", data.Length);
                            Fill("Width", data.Width);
                            Fill("Height", data.Height);
                            Fill("Net Weight", data.NetWeight);
                            Fill("Gross Weight", data.GrossWeight);
                        }

                        int maxQty = dt.AsEnumerable().Where(r => r["QuantityPerCarton"] != DBNull.Value).Max(r => Convert.ToInt32(r["QuantityPerCarton"]));
                        try
                        {
                            var qtyInput = wait.Until(d => d.FindElement(By.XPath("//div[contains(@class,'qtyPerCarton')]//input")));
                            ((IJavaScriptExecutor)driver).ExecuteScript("arguments[0].value = '';", qtyInput);
                            qtyInput.SendKeys(maxQty.ToString());
                        }
                        catch { }
                    }

                    saveDraftBtn.Click();
                }

                lblStatus.Text = "Status: Done!";
                MessageBox.Show("Save complete!");
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message);
            }
        }

        private IWebElement TryWaitCarton(IWebDriver driver, string po)
        {
            try
            {
                var wait = new WebDriverWait(driver, TimeSpan.FromSeconds(10));
                return wait.Until(d => d.FindElement(By.XPath($"//div[@class='carton'][.//div[@class='po-number' and normalize-space()='{po}']]")));
            }
            catch { return null; }
        }

        public class CartonData
        {
            public string PO { get; set; }
            public string Length { get; set; }
            public string Width { get; set; }
            public string Height { get; set; }
            public string NetWeight { get; set; }
            public string GrossWeight { get; set; }
        }

        private void Photo8Form_FormClosing(object sender, FormClosingEventArgs e)
        {
            if (driver != null) { driver.Quit(); driver = null; }
        }

        private void TxtImagePath_TextChanged(object sender, EventArgs e)
        {
            Properties.Settings.Default.Image = txtImagePath.Text;
            Properties.Settings.Default.Save();
        }

        private void TxtType_TextChanged(object sender, EventArgs e)
        {
            Properties.Settings.Default.Type = txtType.Text;
            Properties.Settings.Default.Save();
        }

        private void TxtSeason_TextChanged(object sender, EventArgs e)
        {
            Properties.Settings.Default.Season = txtSeason.Text;
            Properties.Settings.Default.Save();
        }

        private void TxtContractor_TextChanged(object sender, EventArgs e)
        {
            Properties.Settings.Default.Contractor = txtContractor.Text;
            Properties.Settings.Default.Save();
        }

        private void BtnBack_Click(object sender, EventArgs e)
        {
            this.Close();
        }
    }
}