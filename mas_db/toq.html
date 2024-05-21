<?php include("../head.php") ?>
		<?php

		include("../connect.php");
		//test if connection failed
		if(mysqli_connect_errno()){
    		die("connection failed: "
        		. mysqli_connect_error()
        		. " (" . mysqli_connect_errno()
        		. ")");
		}
		
		$id = 0;
		if (!empty($_GET["id"])) {
			$id = $_GET["id"];
		}
		$y = 0;
		if (!empty($_GET["year"])) {
			$y = $_GET["year"];
		}
		if ($y != 0) {
			if ($y != 1) {
				$query = 'SELECT * FROM mas_db WHERE AASTA=' . $y;
				echo '<h1>Aasta ' . $y . '</h1>';
			} else {
				$query = 'SELECT * FROM mas_db';
				echo '<h1>Kõik versioonid</h1>';
			}
			$result = mysqli_query($connection, $query);
			while ($row = mysqli_fetch_array($result)) {
				$id = $row[0];
				$ver = $row[1];
				$ver_l = $row[2];
				$year = $row[3];
				$name = $row[4];
				$descript = $row[5];
				$mini = $row[6];
				$paper_query = "SELECT DISTINCT * FROM mas_wallpapers LEFT JOIN mas_db ON mas_wallpapers.VERSIOONI_ID WHERE mas_wallpapers.VERSIOONI_ID = " . $id . ";";
				$result2 = mysqli_query($connection, $paper_query);
				echo '<hr/>';
				$last = null;
				$beenhere = array();
				while ($cols = mysqli_fetch_array($result2)) {
					$wallpaper_location = $cols[1];
					if (!in_array($wallpaper_location, $beenhere)) {
                        $wid = $cols[0];
                        if ($wallpaper_location != $last)
                        {
                            echo '<a href="#/" ' . 'onclick="Zoom' . $wid . '();"'  .  '><img id="img' . $wid . '" src="../images/' . $wallpaper_location . '"/></a>';
                            $last = $wallpaper_location;
                        }
                        echo '<script>
                                function Zoom' . $wid .'() {
                                    var image = document.getElementById("img' . $wid . '");
                                    if (image.style.height == "auto")
                                    {
                                        image.style.height = "250px";
                                    }
                                    else {
                                        image.style.height = "auto";
                                    }
                                }
                            </script>';
                        array_push($beenhere, $wallpaper_location);
                    }
				}
				echo '<a href="index.php?id=' . $id . '"><h1>' . $name . '</h1></a>';
				if ($mini == "1") {
					echo '<p>(Miniversioon)</p>';
				}
				if ($ver != $ver_l) {
					echo '<p>Versioon ' . $ver . ' - ' . $ver_l . '</p>';
				} else {
					echo '<p>Versioon ' . $ver . '</p>';
				}
				echo '<p>' . nl2br($descript) . '</p>';
				echo '<p> &copy; ' . $year . ' Markuse asjad</p>';
			}
			echo '<hr/>';
			echo '
				  <div style="text-align: center;">
				  <a href="index.php">Sisukord</a>
				  ';
			echo '<a href="#">Tagasi algusesse</a>
				  </div>';
		}
		else if ($id != 0) {
			$counter = "SELECT * FROM mas_db";
			$cq = mysqli_query($connection, $counter);
			$records = 0;
			while ($row = mysqli_fetch_array($cq)) {
				$records++;
			}
			$paper_query = "SELECT DISTINCT ASUKOHT FROM mas_wallpapers LEFT JOIN mas_db ON mas_wallpapers.VERSIOONI_ID WHERE mas_wallpapers.VERSIOONI_ID = " . $id . ";";
			$result = mysqli_query($connection, $paper_query);
			while ($row = mysqli_fetch_array($result)) {
				$wallpaper_location = $row[0];
                echo '<a href="../images/' . $wallpaper_location .  '"><img src="../images/' . $wallpaper_location . '"/></a>';
			}
			
			$query = "SELECT VERSIOON, LVERSIOON, AASTA, NIMI, KIRJELDUS, MINI FROM mas_db WHERE ID=" . $id;
			$result = mysqli_query($connection, $query);
			while ($row = mysqli_fetch_array($result)) {
				echo '<h1>' . $row[3] . '</h1>';
				if ($row[5] == "1") {
					echo '<p>(Miniversioon)</p>';
				}
				if ($row[0] != $row[1]) {
					echo '<p>Versioon ' . $row[0] . ' - ' . $row[1] . '</p>';
				} else {
					echo '<p>Versioon ' . $row[0] . '</p>';
				}
				echo '<p>' . nl2br($row[4]) . '</p>';
				echo '<p> &copy; ' . $row[2] . ' Markuse asjad</p>';
			}
			$prev = $id - 1;
			$next = $id + 1;
			if ($id > 1) {
				echo '<a href="index.php?id=1">&lt;&lt; Esimene</a>';
				echo '<a href="index.php?id=' . $prev . '">&lt; Eelmine</a>';
			}
			if ($id < $records) {
				echo '<a href="index.php?id=' . $next . '">Järgmine &gt;</a>';
				echo '<a href="index.php?id=' . $records . '">Viimane &gt;&gt;</a>';
			}
			echo '<hr>
				  <div style="text-align: center;">';
			echo '<a href="index.php?year=1">Kõik versioonid</a>';
			echo '<a href="index.php">Sisukord</a>';
			echo '</div>';
		} else {
			$counter = "SELECT * FROM mas_db";
			echo '<h1>Sisukord</h1>
				  <br/>';
			echo '<a href="index.php?year=1">Kuva kõik versioonid</a><br/><br/>';
			echo '<table><tr><th>Versioon(id)</th><th>Nimi</th><th>Aasta</th></tr><tr><td style="text-align: right;">';
			$current = 1;
			$cq = mysqli_query($connection, $counter);
			while ($row = mysqli_fetch_array($cq)) {
				if ($row[1] != $row[2]) {
					echo '<a href="index.php?id=' . $current . '">' . $row[1] . ' - ' . $row[2] . '</a><br/>';
				} else {
					echo '<a href="index.php?id=' . $current . '">' . $row[1]. '</a><br/>';
				}
				$current++;
			}
			echo '</td><td>';
			$current = 1;
			$cq = mysqli_query($connection, $counter);
			while ($row = mysqli_fetch_array($cq)) {
				$mini = $row[6];
				$suffix = "";
				if ($mini == "1") {
					$suffix = " [M]";	
				}
				echo '<a href="index.php?id=' . $current . '">' . $row[4]  . $suffix .  '</a><br/>';
				$current++;
			}
			$cq = mysqli_query($connection, $counter);
			echo '</td><td>';
			while ($row = mysqli_fetch_array($cq)) {
				echo '<a href="index.php?year=' . $row[3] . '">' . $row[3] . '</a><br/>';
			}
			echo '</td></tr></table>';
		}
		?>

<?php include("../foot.php"); ?>
