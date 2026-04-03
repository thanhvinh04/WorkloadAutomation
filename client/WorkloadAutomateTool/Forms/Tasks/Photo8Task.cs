using OpenQA.Selenium;
using OpenQA.Selenium.Chrome;
using OpenQA.Selenium.Support.UI;
using System;
using System.Windows.Forms;
using SeleniumExtras.WaitHelpers;
using System.Collections.Generic;
using System.Linq;
using System.Drawing;
using System.Data.SqlClient;
using System.Data;
using System.Configuration;
using System.IO;
using System.Text.RegularExpressions;
using System.Threading;
using WorkloadAutomateTool.Services;

namespace WorkloadAutomateTool.Forms.Tasks
{
    public partial class Photo8Task : Form
    {
        private IWebDriver driver;
        private int checkProcess;
        private DataTable dt = new DataTable();
        private string customerCode;

        public Photo8Task(string customer = "HADDAD")
        {
            InitializeComponent();
            this.customerCode = customer;
            checkProcess = 0;
            txtImagePath.Text = Properties.Settings.Default.Image;
            txtType.Text = Properties.Settings.Default.Type;
            txtContractor.Text = Properties.Settings.Default.Contractor;
            txtSeason.Text = Properties.Settings.Default.Season;
            lblCustomerName.Text = customer;
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
                dialog.Description = "Select Chrome Selenium Profile folder";
                dialog.ShowNewFolderButton = true;

                if (dialog.ShowDialog() != DialogResult.OK)
                    throw new Exception("Please select a folder for Chrome profile.");

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
                fbd.Description = "Select folder containing images";
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

                string baseUrl = GetBaseUrlForCustomer(customerCode);
                driver.Navigate().GoToUrl(baseUrl);
                lblStatus.Text = "Status: Login Success!";
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

        private string GetBaseUrlForCustomer(string customer)
        {
            switch (customer)
            {
                case "HADDAD":
                    return "https://workloadautomation.haddad.com/";
                case "LTD":
                    return "https://workloadautomation.ltd.com/";
                case "GARAN":
                    return "https://workloadautomation.garan.com/";
                default:
                    return "https://workloadautomation.haddad.com/";
            }
        }

        private void BtnLoadTasks_Click(object sender, EventArgs e)
        {
            try
            {
                if (driver == null)
                {
                    MessageBox.Show("Please login first!");
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
                    MessageBox.Show("Please enter Contractor-ContractNo-Season-Label or PO list");
                    return;
                }

                lblStatus.Text = "Status: Processing...";

                if (poList.Count == 0)
                {
                    var parameters = labelList
                        .Select((label, index) => $"@p{index}")
                        .ToList();

                    string sql = $@"
                    SELECT
                        PurchaseOrderNumber
                        ,CASE WHEN Season = 'M' THEN 'Summer '
                              WHEN Season = 'F' THEN 'Fall '
                              WHEN Season = 'S' THEN 'Spring '
                              WHEN Season = 'H' THEN 'Holiday '
                            END + cast(Year as nvarchar(4)) Season
                        ,ContractNo
                        ,CustomerStyle
                        ,FORMAT(ShipDate, 'MMM dd, yyyy', 'en-US') AS ShipDateText
                        ,ColorCode
                        ,LabelCode
                        ,Account
                        ,Contractor
                        ,Length
                        ,Width
                        ,Height
                        ,NetWeight
                        ,GrossWeight
                        ,QuantityPerCarton
                    FROM ItemStyle i
                    LEFT JOIN 
                    (
                        SELECT 
                            LSStyle,MAX(TRY_CAST(Length as float)) Length
                            ,MAX(TRY_CAST(Width as float)) Width
                            ,MAX(TRY_CAST(Height as float)) Height
                            ,MAX(TRY_CAST(NetWeight as float)) NetWeight
                            ,MAX(TRY_CAST(GrossWeight as float)) GrossWeight
                            ,MAX(TRY_CAST(QuantityPerCarton as float)) QuantityPerCarton
                        FROM PackingLine
                        WHERE IsDeleted = 0
                        GROUP BY LSStyle
                    )p ON p.LSStyle = i.LSStyle AND i.IsDeleted = 0 AND ISNULL(ItemStyleStatusCode,1) <> 3
                    WHERE LabelCode IN ({string.Join(",", parameters)})
                    AND ContractNo = '{contractNo}'
                    AND Contractor = '{contractor}'
                    AND (Season + right(cast(Year as nvarchar(4)),2) = '{season}'
                    OR Season + cast(Year as nvarchar(4)) = '{season}')
                    ";

                    string connStr = ConfigurationManager
                        .ConnectionStrings["MyDbConnectionPro"]
                        .ConnectionString;
                    using (SqlConnection conn = new SqlConnection(connStr))
                    using (SqlCommand cmd = new SqlCommand(sql, conn))
                    {
                        for (int i = 0; i < labelList.Count; i++)
                        {
                            cmd.Parameters.AddWithValue($"@p{i}", labelList[i]);
                        }

                        conn.Open();

                        using (SqlDataAdapter da = new SqlDataAdapter(cmd))
                        {
                            da.Fill(dt);
                        }
                    }
                }
                else
                {
                    var parameters = poList
                        .Select((po, index) => $"@p{index}")
                        .ToList();

                    string sql = $@"
                    SELECT
                        PurchaseOrderNumber
                        ,CASE WHEN Season = 'M' THEN 'Summer '
                              WHEN Season = 'F' THEN 'Fall '
                              WHEN Season = 'S' THEN 'Spring '
                              WHEN Season = 'H' THEN 'Holiday '
                            END + cast(Year as nvarchar(4)) Season
                        ,ContractNo
                        ,CustomerStyle
                        ,FORMAT(ShipDate, 'MMM dd, yyyy', 'en-US') AS ShipDateText
                        ,ColorCode
                        ,LabelCode
                        ,Account
                        ,Contractor
                        ,Length
                        ,Width
                        ,Height
                        ,NetWeight
                        ,GrossWeight
                        ,QuantityPerCarton
                    FROM ItemStyle i
                    LEFT JOIN 
                    (
                        SELECT 
                            LSStyle,MAX(TRY_CAST(Length as float)) Length
                            ,MAX(TRY_CAST(Width as float)) Width
                            ,MAX(TRY_CAST(Height as float)) Height
                            ,MAX(TRY_CAST(NetWeight as float)) NetWeight
                            ,MAX(TRY_CAST(GrossWeight as float)) GrossWeight
                            ,MAX(TRY_CAST(QuantityPerCarton as float)) QuantityPerCarton
                        FROM PackingLine
                        WHERE IsDeleted = 0
                        GROUP BY LSStyle
                    )p ON p.LSStyle = i.LSStyle AND i.IsDeleted = 0 AND ISNULL(ItemStyleStatusCode,1) <> 3
                    WHERE PurchaseOrderNumber IN ({string.Join(",", parameters)})
                    ";

                    string connStr = ConfigurationManager
                        .ConnectionStrings["MyDbConnectionPro"]
                        .ConnectionString;
                    using (SqlConnection conn = new SqlConnection(connStr))
                    using (SqlCommand cmd = new SqlCommand(sql, conn))
                    {
                        for (int i = 0; i < poList.Count; i++)
                        {
                            cmd.Parameters.AddWithValue($"@p{i}", poList[i]);
                        }

                        conn.Open();

                        using (SqlDataAdapter da = new SqlDataAdapter(cmd))
                        {
                            da.Fill(dt);
                        }
                    }
                }
                dataGridView1.DataSource = dt;
                if (dt.Rows.Count == 0)
                {
                    MessageBox.Show("No data found!");
                    return;
                }

                var type = txtType.Text.ToUpper();
                if (type != "HBNYO" && type != "HBE")
                {
                    MessageBox.Show("Invalid Type!");
                    return;
                }

                string baseUrl = GetBaseUrlForCustomer(customerCode);
                driver.Navigate().GoToUrl(baseUrl + "Create");
                WebDriverWait wait = new WebDriverWait(driver, TimeSpan.FromSeconds(100));
                var typebutton = wait.Until(d =>
                    d.FindElement(By.XPath("//button[contains(., '" + type + "')]"))
                );
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
                if (driver != null)
                {
                    driver.Quit();
                    driver = null;
                }
            }
        }

        private void FillCreateRequest(DataTable dt)
        {
            WebDriverWait wait = new WebDriverWait(driver, TimeSpan.FromSeconds(100));
            lblStatus.Text = "Status: Fill Draft...";

            var Season = dt.AsEnumerable()
                 .Select(r => r["Season"].ToString())
                 .FirstOrDefault();

            var dropdown = wait.Until(d =>
                d.FindElement(By.XPath("//div[contains(@class,'rw-dropdown-list-input')]"))
            );
            dropdown.Click();
            var input = wait.Until(d =>
                d.FindElement(By.XPath("//div[contains(@class,'rw-input')]//input[not(@tabindex='-1')]"))
            );
            wait.Until(ExpectedConditions.ElementToBeClickable(input));
            input.SendKeys(Season);
            input.SendKeys(OpenQA.Selenium.Keys.Enter);

            lblStatus.Text = "Status: Fill Factory...";

            var Factory = dt.AsEnumerable()
                 .Select(r => r["Contractor"].ToString())
                 .Distinct()
                 .First();
            input = driver.FindElement(By.CssSelector(".searchable-dropdown input"));
            input.Clear();
            input.SendKeys(Factory);
            input.SendKeys(OpenQA.Selenium.Keys.Enter);

            lblStatus.Text = "Status: Fill Reference Number...";

            var refInput = driver.FindElement(By.XPath("//div[@class='field-label' and text()='Reference Number']/following::input[1]"));
            var refText = dt.AsEnumerable()
                 .Select(r => r["ContractNo"].ToString())
                 .FirstOrDefault();
            refInput.Click();
            refInput.Clear();
            refInput.SendKeys(refText);
            refInput.SendKeys(OpenQA.Selenium.Keys.Enter);

            lblStatus.Text = "Status: Fill Colors...";

            List<string> colors = dt.AsEnumerable()
                 .Select(r => r["ColorCode"].ToString())
                 .Distinct()
                 .ToList();

            foreach (var color in colors)
            {
                var Colorinput = wait.Until(d =>
                    d.FindElement(By.XPath(
                        "//div[@class='field-label' and normalize-space()='Colors']" +
                        "/following-sibling::div" +
                        "//div[contains(@class,'searchable-dropdown')]//input"
                    ))
                );

                Colorinput.Click();
                Colorinput.Clear();
                Colorinput.SendKeys(color);
                Colorinput.SendKeys(OpenQA.Selenium.Keys.Enter);

                wait.Until(d =>
                {
                    var selected = d.FindElements(
                        By.XPath("//div[contains(@class,'selected-items')]//div[contains(@class,'selected-item')]//div[@class='value']")
                    );
                    return selected.Any(s => s.Text.Trim().Equals(color, StringComparison.OrdinalIgnoreCase));
                });
            }

            lblStatus.Text = "Status: Fill Styles...";

            List<string> Styles = dt.AsEnumerable()
                 .Select(r => r["CustomerStyle"].ToString())
                 .Distinct()
                 .ToList();
            var Styleinput = wait.Until(d =>
                    d.FindElement(By.XPath(
                        "//div[@class='field-label' and normalize-space()='Styles']" +
                        "/following-sibling::div" +
                        "//div[contains(@class,'searchable-dropdown')]//input"
                    ))
                );

            foreach (var Style in Styles)
            {
                Styleinput = wait.Until(d =>
                    d.FindElement(By.XPath(
                        "//div[@class='field-label' and normalize-space()='Styles']" +
                        "/following-sibling::div" +
                        "//div[contains(@class,'searchable-dropdown')]//input"
                    ))
                );
                Styleinput.Click();
                Styleinput.SendKeys(Style);
                Styleinput.SendKeys(OpenQA.Selenium.Keys.Enter);

                wait.Until(d =>
                {
                    Styleinput.SendKeys(OpenQA.Selenium.Keys.Enter);
                    var selected = d.FindElements(
                        By.XPath("//div[contains(@class,'selected-items')]//div[contains(@class,'selected-item')]//div[@class='value']")
                    );
                    return selected.Any(s => s.Text.Trim().Equals(Style, StringComparison.OrdinalIgnoreCase));
                });
            }

            lblStatus.Text = "Status: Fill Labels...";

            List<string> Labels = dt.AsEnumerable()
                 .Select(r => r["LabelCode"].ToString())
                 .Distinct()
                 .ToList();

            foreach (var label in Labels)
            {
                var Labelinput = wait.Until(d =>
                    d.FindElement(By.XPath(
                        "//div[@class='field-label' and normalize-space()='Labels']" +
                        "/following-sibling::div" +
                        "//div[contains(@class,'searchable-dropdown')]//input"
                    ))
                );

                Labelinput.Click();
                Labelinput.SendKeys(label);
                Labelinput.SendKeys(OpenQA.Selenium.Keys.Enter);

                wait.Until(d =>
                {
                    var selected = d.FindElements(
                        By.XPath("//div[contains(@class,'selected-items')]//div[contains(@class,'selected-item')]//div[@class='value']")
                    );
                    return selected.Any(s => s.Text.Trim().Equals(label, StringComparison.OrdinalIgnoreCase));
                });
            }

            lblStatus.Text = "Status: Fill ShipDate...";

            var shipdate = dt.AsEnumerable()
                 .Select(r => r["ShipDateText"].ToString())
                 .Distinct()
                 .ToList();
            int i = 1;
            foreach (var ship in shipdate)
            {
                var shipDate1 = wait.Until(d =>
                d.FindElement(By.XPath("//div[@class='field-label' and normalize-space()='Ship Dates']/following::input[" + i + "]"))
                );
                shipDate1.Click();
                shipDate1.SendKeys(ship);
                shipDate1.SendKeys(OpenQA.Selenium.Keys.Enter);
                Styleinput.Click();
                i++;
            }

            lblStatus.Text = "Status: Fill Customer...";

            var customerInput = wait.Until(d =>
                d.FindElement(By.XPath("//div[@class='field-label' and normalize-space()='Customer']/following::div[contains(@class,'searchable-dropdown')]//input"))
            );

            customerInput.Click();
            customerInput.Clear();

            string customerName = dt.AsEnumerable()
                 .Select(r => r["Account"].ToString())
                 .FirstOrDefault();

            customerInput.SendKeys(customerName);
            customerInput.SendKeys(OpenQA.Selenium.Keys.Enter);

            var firstItem = wait.Until(ExpectedConditions.ElementToBeClickable(
                By.XPath("(//div[contains(@class,'list')]//div[contains(@class,'item')])[1]")));
            firstItem.Click();

            lblStatus.Text = "Status: Select POs...";

            List<string> poList = dt.AsEnumerable()
                 .Select(r => r["PurchaseOrderNumber"].ToString())
                 .Distinct()
                 .ToList();
            wait.Until(d => d.FindElements(By.CssSelector(".checkbox-list input[type='checkbox']")).Count > 0);

            foreach (var po in poList)
            {
                try
                {
                    var checkbox = driver.FindElement(By.Id(po));

                    if (!checkbox.Selected)
                    {
                        ((IJavaScriptExecutor)driver)
                            .ExecuteScript("arguments[0].click();", checkbox);
                    }
                }
                catch { }
            }
        }

        private void BtnSave_Click(object sender, EventArgs e)
        {
            try
            {
                if (checkProcess == 1)
                {
                    MessageBox.Show("Need Load Draft before!");
                }
                else if (checkProcess == 2)
                {
                    WebDriverWait wait = new WebDriverWait(driver, TimeSpan.FromSeconds(100));
                    var saveDraftBtn = wait.Until(d =>
                        d.FindElement(By.XPath(
                            "//div[contains(@class,'default-header')]//button[normalize-space()='Save Draft']"))
                    );
                    saveDraftBtn.Click();

                    bool isError = false;

                    wait.Until(d =>
                    {
                        if (d.Url.Contains("/Details/GeneralInfo"))
                        {
                            return true;
                        }

                        var error = d.FindElements(By.XPath(
                            "//div[contains(@class,'message-modal') and contains(.,' was not saved')]"
                        ));

                        if (error.Any())
                        {
                            isError = true;
                            return true;
                        }

                        return false;
                    });

                    if (isError)
                    {
                        MessageBox.Show("Save Draft failed! Please check again your information.");
                        return;
                    }

                    string currentUrl = driver.Url;
                    while (!currentUrl.Contains("Details"))
                    {
                        currentUrl = driver.Url;
                    }

                    string baseUrl = Regex.Match(currentUrl, @"^.+?/Details").Value;
                    var Tags = new List<string>
                    {
                        "Components",
                        "Packing",
                        "Garment",
                        "ClosedCarton"
                    };
                    foreach (var tag in Tags)
                    {
                        string tagUrl = baseUrl + $"/{tag}";

                        driver.Navigate().GoToUrl(tagUrl);
                        wait = new WebDriverWait(driver, TimeSpan.FromSeconds(100));
                        var groupNames = wait.Until(d =>
                        {
                            var els = d.FindElements(By.XPath("//div[@class='group-name']"));
                            return els.Count > 0 ? els : null;
                        });

                        List<string> groupNameTexts = groupNames
                            .Select(g => g.Text.Trim())
                            .Where(t => !string.IsNullOrEmpty(t))
                            .ToList();

                        foreach (var groupName in groupNameTexts)
                        {
                            var files = Directory.GetFiles(txtImagePath.Text)
                                .Where(f => Path.GetFileName(f)
                                .StartsWith(groupName.Trim(), StringComparison.OrdinalIgnoreCase))
                                .ToArray();
                            if (files.Length == 0)
                                continue;
                            var attachments = wait.Until(d =>
                                    d.FindElement(By.XPath(
                                        $"//div[@class='group']" +
                                        $"[.//div[@class='group-name' and " +
                                        $"translate(normalize-space(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz') = '{groupName.ToLower()}']]" +
                                        $"//div[@class='attachments']"
                                    ))
                                );
                            var tiles = attachments.FindElement(
                                By.XPath("./div[@class='tiles']")
                            );
                            ((IJavaScriptExecutor)driver)
                                .ExecuteScript("arguments[0].scrollIntoView({block:'center'});", tiles);

                            ((IJavaScriptExecutor)driver)
                                .ExecuteScript("arguments[0].click();", tiles);

                            var modal = wait.Until(d =>
                            {
                                var ms = d.FindElements(By.XPath("//div[contains(@class,'upload-file-modal')]"));
                                return ms.FirstOrDefault(x => x.Displayed);
                            });

                            var fileInput = wait.Until(d =>
                                modal.FindElement(By.XPath(".//input[@type='file']"))
                            );

                            ((IJavaScriptExecutor)driver)
                                .ExecuteScript("arguments[0].style.display='block'; arguments[0].value='';", fileInput);

                            fileInput.SendKeys(string.Join("\n", files));

                            var saveBtn = wait.Until(
                                ExpectedConditions.ElementToBeClickable(
                                    By.XPath("//div[contains(@class,'upload-file-modal')]//button[normalize-space()='Save']")
                                )
                            );

                            ((IJavaScriptExecutor)driver)
                                .ExecuteScript("arguments[0].click();", saveBtn);
                            wait.Until(d =>
                            {
                                var ms = d.FindElements(By.XPath("//div[contains(@class,'upload-file-modal')]"));
                                return ms.Count == 0 || ms.All(x => !x.Displayed);
                            });
                            wait.Until(d =>
                            {
                                var curtains = d.FindElements(By.CssSelector("div.curtain"));
                                return curtains.Count == 0 || curtains.All(c => !c.Displayed);
                            });
                            wait.Until(d =>
                            {
                                return ((IJavaScriptExecutor)d)
                                    .ExecuteScript("return document.readyState")
                                    .ToString() == "complete";
                            });
                        }
                        saveDraftBtn = wait.Until(
                            ExpectedConditions.ElementToBeClickable(
                                By.XPath("//button[normalize-space()='Save Draft']")
                            )
                        );
                        ((IJavaScriptExecutor)driver)
                            .ExecuteScript("arguments[0].scrollIntoView({block:'center'});", saveDraftBtn);
                        Thread.Sleep(2000);
                        if (tag == "ClosedCarton")
                        {
                            List<CartonData> cartons = new List<CartonData>();

                            foreach (DataRow row in dt.Rows)
                            {
                                if (row["PurchaseOrderNumber"] == DBNull.Value)
                                    continue;

                                var carton = new CartonData
                                {
                                    PO = row["PurchaseOrderNumber"].ToString().Trim(),
                                    Length = row["Length"]?.ToString(),
                                    Width = row["Width"]?.ToString(),
                                    Height = row["Height"]?.ToString(),
                                    NetWeight = row["NetWeight"]?.ToString(),
                                    GrossWeight = row["GrossWeight"]?.ToString()
                                };

                                cartons.Add(carton);
                            }
                            foreach (var data in cartons)
                            {
                                var carton = TryWaitCarton(driver, data.PO);
                                if (carton == null)
                                {
                                    Console.WriteLine($"PO {data.PO} not found -> skipped");
                                    return;
                                }

                                void Fill(string label, string value)
                                {
                                    if (string.IsNullOrWhiteSpace(value)) return;

                                    try
                                    {
                                        var input = carton.FindElement(By.XPath(
                                            $".//div[@class='field'][.//div[text()='{label}']]//input"
                                        ));

                                        ((IJavaScriptExecutor)driver)
                                            .ExecuteScript("arguments[0].value = '';", input);

                                        input.SendKeys(value);
                                    }
                                    catch (NoSuchElementException)
                                    {
                                        Console.WriteLine($"Field '{label}' not found for PO {data.PO}");
                                    }
                                }

                                Fill("Length", data.Length);
                                Fill("Width", data.Width);
                                Fill("Height", data.Height);
                                Fill("Net Weight", data.NetWeight);
                                Fill("Gross Weight", data.GrossWeight);
                            }
                            int maxQty = dt.AsEnumerable()
                            .Where(r => r["QuantityPerCarton"] != DBNull.Value)
                            .Max(r => Convert.ToInt32(r["QuantityPerCarton"]));
                            try
                            {
                                var qtyInput = wait.Until(d =>
                                    d.FindElement(By.XPath("//div[contains(@class,'qtyPerCarton')]//input"))
                                );

                                ((IJavaScriptExecutor)driver)
                                    .ExecuteScript("arguments[0].value = '';", qtyInput);

                                qtyInput.SendKeys(maxQty.ToString());
                            }
                            catch (NoSuchElementException)
                            {
                                Console.WriteLine($"Field 'QuantityPerCarton' not found");
                            }
                        }
                        saveDraftBtn.Click();
                    }
                }
                else
                {
                    MessageBox.Show("Need Login and Load Draft before!");
                }
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
                return wait.Until(d =>
                    d.FindElement(By.XPath(
                        $"//div[@class='carton'][.//div[@class='po-number' and normalize-space()='{po}']]"
                    ))
                );
            }
            catch (WebDriverTimeoutException)
            {
                return null;
            }
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

        private void Photo8Task_FormClosing(object sender, FormClosingEventArgs e)
        {
            if (driver != null)
            {
                driver.Quit();
                driver = null;
            }
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

        private async void BtnUploadToServer_Click(object sender, EventArgs e)
        {
            if (string.IsNullOrWhiteSpace(txtImagePath.Text))
            {
                MessageBox.Show("Please select image folder first!");
                return;
            }

            try
            {
                lblStatus.Text = "Status: Uploading to server...";
                
                var files = Directory.GetFiles(txtImagePath.Text);
                var result = await ApiService.UploadFilesAsync(files, customerCode);
                
                if (result.Success)
                {
                    lblStatus.Text = "Status: Upload complete! Waiting for result...";
                    MessageBox.Show($"Files uploaded successfully. Job ID: {result.JobId}");
                    
                    if (!string.IsNullOrEmpty(result.JobId))
                    {
                        PollForResult(result.JobId);
                    }
                }
                else
                {
                    lblStatus.Text = "Status: Upload failed!";
                    MessageBox.Show($"Upload failed: {result.ErrorMessage}");
                }
            }
            catch (Exception ex)
            {
                lblStatus.Text = "Status: Error!";
                MessageBox.Show(ex.Message);
            }
        }

        private async void PollForResult(string jobId)
        {
            try
            {
                lblStatus.Text = "Status: Processing on server...";
                
                var result = await ApiService.PollJobResultAsync(jobId);
                
                if (result.Success && result.HasResult)
                {
                    lblStatus.Text = "Status: Result received!";
                    MessageBox.Show($"Result received: {result.ResultFilePath}");
                    
                    if (!string.IsNullOrEmpty(result.ResultFilePath) && File.Exists(result.ResultFilePath))
                    {
                        System.Diagnostics.Process.Start(result.ResultFilePath);
                    }
                }
                else if (!result.Success)
                {
                    lblStatus.Text = "Status: Error getting result!";
                    MessageBox.Show($"Error: {result.ErrorMessage}");
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message);
            }
        }

        private void BtnBack_Click(object sender, EventArgs e)
        {
            this.Close();
        }
    }
}