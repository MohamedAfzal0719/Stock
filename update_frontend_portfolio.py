import re

def update_frontend():
    with open('d:/Goldbees/frontend/src/app/page.js', 'r', encoding='utf-8') as f:
        content = f.read()

    # We need to inject useUser
    if "const { isLoaded, isSignedIn, user } = useUser();" not in content:
        # Find where state hooks start, e.g., const [activeTab, setActiveTab] = useState('overview');
        content = content.replace("const [activeTab, setActiveTab] = useState('overview');",
                                  "const { isLoaded, isSignedIn, user } = useUser();\n  const [activeTab, setActiveTab] = useState('overview');")

    # The existing portfolio state is likely:
    # const [investedAmount, setInvestedAmount] = useState('');
    # const [unitsHeld, setUnitsHeld] = useState('');
    # We will add a save function and a useEffect hook.
    
    portfolio_logic = """
  const [isSavingPortfolio, setIsSavingPortfolio] = useState(false);
  const [portfolioSaved, setPortfolioSaved] = useState(false);

  useEffect(() => {
    if (isLoaded && isSignedIn && user) {
      // Fetch user's saved portfolio
      fetch(`http://localhost:8000/portfolio/${user.id}`)
        .then(res => res.json())
        .then(data => {
          if (data.status === 'success') {
            if (data.data.invested_amount > 0) setInvestedAmount(data.data.invested_amount.toString());
            if (data.data.units_held > 0) setUnitsHeld(data.data.units_held.toString());
          }
        })
        .catch(err => console.error("Error fetching portfolio:", err));
    }
  }, [isLoaded, isSignedIn, user]);

  const savePortfolio = async () => {
    if (!isSignedIn || !user) return;
    setIsSavingPortfolio(true);
    setPortfolioSaved(false);
    try {
      await fetch(`http://localhost:8000/portfolio/${user.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          invested_amount: parseFloat(investedAmount) || 0,
          units_held: parseFloat(unitsHeld) || 0
        })
      });
      setPortfolioSaved(true);
      setTimeout(() => setPortfolioSaved(false), 3000);
    } catch (err) {
      console.error("Error saving portfolio:", err);
    }
    setIsSavingPortfolio(false);
  };
"""
    if "const savePortfolio = async" not in content:
        content = content.replace("const fetchDashboardData = async () => {", portfolio_logic + "\n  const fetchDashboardData = async () => {")

    # Add the save button to the UI
    # We need to find the "Personal Portfolio Tracker" section.
    # It probably looks like: <h2 className="text-xl font-semibold mb-4 flex items-center text-gray-200">
    #                             <Briefcase className="mr-2 text-indigo-400 w-6 h-6" /> Personal Portfolio Tracker
    #                         </h2>
    # We can inject a Save button below the inputs.
    
    ui_find = '<Briefcase className="mr-2 text-indigo-400 w-6 h-6" /> Personal Portfolio Tracker'
    if ui_find in content and "savePortfolio" not in content.split(ui_find)[1][:1000]:
        # Let's replace the ending of the input fields section
        # Look for the last input field which is usually total units
        units_input = 'onChange={(e) => setUnitsHeld(e.target.value)}'
        
        replacement = units_input + """
              />
            </div>
            
            <div className="mt-4 flex items-center space-x-4">
              <button 
                onClick={savePortfolio}
                disabled={isSavingPortfolio}
                className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg font-semibold transition-colors disabled:opacity-50"
              >
                {isSavingPortfolio ? 'Saving...' : 'Save Portfolio'}
              </button>
              {portfolioSaved && <span className="text-emerald-400 text-sm font-medium">Saved to your account! ✓</span>}
            </div>"""
        
        # We need to be careful. Let's just use regex to insert after the unitsHeld input block.
        content = re.sub(r'(onChange=\{\(e\) => setUnitsHeld\(e\.target\.value\)\}\s*/>\s*</div>)', r'\1\n            <div className="mt-4 flex items-center space-x-4">\n              <button onClick={savePortfolio} disabled={isSavingPortfolio} className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg font-semibold transition-colors disabled:opacity-50">{isSavingPortfolio ? "Saving..." : "Save Portfolio"}</button>\n              {portfolioSaved && <span className="text-emerald-400 text-sm font-medium">Saved to your account! ✓</span>}\n            </div>', content)

    with open('d:/Goldbees/frontend/src/app/page.js', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    update_frontend()
