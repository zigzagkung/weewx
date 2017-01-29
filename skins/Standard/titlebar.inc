## current module for standard skin
## Copyright Tom Keffer, Matthew Wall
## See LICENSE.txt for your rights

<div id="title_bar">
  <div id="title">
    <h1 class="page_title">$station.location</h1>
    <p class="lastupdate">$current.dateTime</p>
  </div>
  <div id="rss_link"><a href="rss.xml">RSS</a></div>
  <div id="reports">
    Monthly Reports:
    <select name="reports" onchange="openNOAAFile(value)">
      #for $monthYear in $SummaryByMonth
      <option value="$monthYear">$monthYear</option>
      #end for
      <option selected>- Select Month -</option>
    </select>
    <br/>
    Yearly Reports:
    <select name="reports" onchange="openNOAAFile(value)">
      #for $yr in $SummaryByYear
      <option value="$yr">$yr</option>
      #end for
      <option selected>- Select Year -</option>
    </select>
  </div>
</div>